import argparse
import json
import sys
import unittest
from concurrent.futures import Future
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import tts_worker_next as worker


class MossRulesTest(unittest.TestCase):
    def setUp(self):
        self.cfg = worker.load_config(Path(__file__).with_name("tts_config_moss.json"))

    def clip(self, lid, send, *, lang="zh", brisk=False, **metadata):
        clip = dict(_lid=lid, lang=lang, send=send, **metadata)
        worker.prepare_moss_clip(clip, brisk=brisk)
        return clip

    def test_poem_pauses_mood_and_duration(self):
        send = "静夜思。李白。床前明月光，疑是地上霜。举头望明月，低头思故乡。"
        clip = self.clip("yuwen/yw-tang-poems", send, mood="light")
        self.assertEqual((clip["kind"], clip["pace"]), ("poem", 2.7))
        self.assertEqual(clip["text"], "静夜思。[pause 1.0s]李白。[pause 1.0s]"
                         "床前明月光，疑是地上霜。[pause 0.8s]举头望明月，低头思故乡。")
        self.assertEqual(worker.moss_item(clip, 0, self.cfg)["tokens"], 139)
        long_poem = self.clip("yuwen/yw-song-ci", "月" * 101, mood="somber")
        self.assertEqual(long_poem["pace"], 2.8)

    def test_science_pauses_and_retry_schedule(self):
        send = "热量从温度较高的物体传向温度较低的物体。这个过程称为热传递。"
        clip = self.clip("physics/heat", send)
        self.assertEqual((clip["kind"], clip["pace"]), ("explain", 3.8))
        self.assertEqual(clip["text"], send.replace("。", "。[pause 0.8s]", 1))
        self.assertEqual([worker.moss_item(clip, n, self.cfg)["tokens"] for n in range(5)],
                         [None, None, None, 96, 96])

    def test_everyday_and_spoken_hook(self):
        send = "今天怎么去学校？我们一起走路。"
        with patch.object(worker, "spoken", return_value="今天怎么去学校？我们步行。"):
            clip = self.clip("life/walk", send, brisk=True)
        self.assertEqual((clip["kind"], clip["pace"]), ("explain", 4.1))
        self.assertEqual(clip["text"], "今天怎么去学校？[pause 0.8s]我们步行。")
        self.assertEqual(clip["send"], send)
        self.assertIsNone(worker.moss_item(clip, 0, self.cfg)["tokens"])
        self.assertEqual(worker.moss_item(clip, 3, self.cfg)["tokens"], 44)
        self.assertEqual(self.clip("life/walk", send)["pace"], 4.0)

    def test_english_pauses_and_duration_without_qa_pace(self):
        clip = self.clip("yuwen/yw-tang-poems", "Look up. Look down.", lang="en", brisk=True)
        self.assertEqual((clip["kind"], clip["pace"]), ("en", None))
        self.assertEqual(clip["text"], "Look up.[pause 0.8s] Look down.")
        self.assertIsNone(worker.moss_item(clip, 0, self.cfg)["tokens"])
        self.assertEqual(worker.moss_item(clip, 3, self.cfg)["tokens"], 48)
        clip["mood"] = "somber"
        self.assertEqual(worker.moss_item(clip, 0, self.cfg)["tokens"], 48)

    def test_record_langs_filter_and_qwen_default(self):
        clips = [{"lang": lang, "key": lang, "send": text}
                 for lang, text in (("en", "A test."), ("zh", "测试。"))]
        data = json.dumps({"clips": clips}).encode()
        entry = dict(id="life/walk", repo="repo", fingerprint=worker.fp12(data), pace="brisk")
        args = argparse.Namespace(fake=True)
        for engine, expected in (("moss", ["zh"]), ("qwen", ["en", "zh"]), (None, ["en", "zh"])):
            with self.subTest(engine=engine):
                cfg = dict(self.cfg, engine=engine)
                if engine is None:
                    del cfg["engine"]
                instance = worker.Worker(cfg, args)
                instance.repos["repo"] = SimpleNamespace(
                    path=Path(self._testMethodName), lessons={}, ledger={}, failed={}
                )
                with patch.object(worker, "fetch", return_value=data):
                    job = instance.prep_lesson(entry, "run")
                self.assertEqual(set(job["want"]), {("en", "en"), ("zh", "zh")})
                self.assertEqual([c["lang"] for c in job["todo"]], expected)
                self.assertTrue(all(c["_lid"] == entry["id"] for c in job["todo"]))
                if engine == "moss":
                    self.assertEqual(job["todo"][0]["pace"], 4.1)

        instance = worker.Worker(dict(self.cfg, record_langs=["zh", "en"]), args)
        prior = dict(record_langs=["zh"], fingerprint=entry["fingerprint"], label="finished", verified="yes")
        instance.repos["repo"] = SimpleNamespace(lessons={entry["id"]: prior})
        self.assertTrue(instance.needs_work(entry))

    def test_oom_split_keeps_moss_items_aligned(self):
        instance = worker.Worker(self.cfg, argparse.Namespace(fake=True))
        clips = [self.clip(lid, "共同的句子。", key="same")
                 for lid in ("life/walk", "physics/heat", "yuwen/yw-song-ci")]
        for clip in clips:
            clip["_item"] = worker.moss_item(clip, 0, self.cfg)
        synth = instance.synths[0]

        def generate(items, lang, timeout, slow):
            self.assertEqual(lang, "zh")
            if len(items) > 1:
                raise worker.GpuOOM("test OOM")
            return [b"\x01\x00" if items[0]["kind"] == "poem" else None], 24000

        with patch.object(synth, "say", side_effect=generate) as say, patch.object(worker, "log"):
            results = instance.run_chunk(clips)
        self.assertEqual([len(call.args[0]) for call in say.call_args_list], [3, 1, 2, 1, 1])
        self.assertIsInstance(results[0][1], worker.RetryLater)
        self.assertIsInstance(results[1][1], worker.RetryLater)
        self.assertEqual(results[2][1][:2], (b"\x01\x00", 24000))

    def test_moss_qa_uses_configured_pitch_and_returns_score(self):
        clip = self.clip("physics/heat", "热量从温度较高的物体传向温度较低的物体。")
        cfg = dict(self.cfg, moss=dict(self.cfg["moss"], f0=[180, 290]))
        pitch_check = Mock(return_value=SimpleNamespace(f0=170, reasons=["F0 170 Hz outside 180-290 Hz"]))
        with patch("moss_engine.W.check_clip_qa", pitch_check):
            qa = worker.check_moss_qa(clip, b"\0\0" * 24000, cfg)
        self.assertEqual(qa.f0, 170)
        self.assertEqual(pitch_check.call_args.args[4]["f0_min"], 180)
        self.assertEqual(pitch_check.call_args.args[4]["f0_max"], 290)
        self.assertTrue(any(reason.startswith("pace ") for reason in qa.reasons))
        self.assertEqual(qa.rank, (qa.score,))

    def test_failed_checks_keep_the_lowest_score_after_five_tries(self):
        instance = worker.Worker(self.cfg, argparse.Namespace(fake=True, lesson="", limit=0))
        lid = "physics/heat"
        entry = dict(id=lid, repo="repo", fingerprint="fixture")
        repo = SimpleNamespace(lessons={}, failed={})
        instance.repos["repo"] = repo
        clip = self.clip(lid, "热量从温度较高的物体传向温度较低的物体。", key="test")
        job = dict(repo=repo, lid=lid, ldir=Path(lid), todo=[clip], left=0, changed=0, recorded=0)
        tokens = []
        scores = [19, 11, 13, 14, 17]

        def say(items, lang, timeout, slow):
            tokens.append(items[0]["tokens"])
            return [bytes([len(tokens), 0]) * 24000], 24000

        def submit(fn, clip, pcm, cfg):
            self.assertIs(fn, worker.check_moss_qa)
            attempt = pcm[0]
            result = Future()
            result.set_result(worker.ClipQA(1.0, 4.5, 200, False, (f"failure {attempt}",),
                                            score=scores[attempt - 1]))
            return result

        instance.qa_pool = SimpleNamespace(submit=submit)
        with (
            patch.object(instance, "apply_rerecord", return_value={}),
            patch.object(instance, "prep_lesson", return_value=job),
            patch.object(instance, "review_clip") as review,
            patch.object(instance, "close_lesson") as close,
            patch.object(instance, "add"),
            patch.object(instance.synths[0], "say", side_effect=say),
            patch.object(worker, "to_mp3") as encode,
            patch.object(worker, "log") as log,
        ):
            self.assertEqual(instance.work_through([entry], "run"), 0)
        self.assertEqual(tokens[:3], [None, None, None])
        self.assertEqual(len(tokens), 5)
        self.assertTrue(all(tokens[3:]))
        self.assertEqual(encode.call_args.args[1][0], 2)
        self.assertEqual(review.call_args.args[-2].reasons, ("failure 2",))
        self.assertEqual(review.call_args.args[-1], 5)
        self.assertIn("tries 5", log.call_args.args[0])
        self.assertIn("target duration no", log.call_args.args[0])
        close.assert_called_once_with(job)

    def test_child_loads_moss_once_and_reports_typed_oom(self):
        class OutOfMemoryError(RuntimeError):
            pass

        item = dict(text="测试。", lang="zh", kind="explain", tokens=None)
        empty_cache = Mock()
        torch = SimpleNamespace(OutOfMemoryError=OutOfMemoryError, cuda=SimpleNamespace(empty_cache=empty_cache))
        engine = Mock()
        engine.generate.side_effect = [OutOfMemoryError("allocation failed"), [None], [b"\x01\x00"]]
        constructor = Mock(return_value=engine)
        conn = Mock()
        conn.recv.side_effect = [[item], [item], [item], None]
        with patch.dict(sys.modules, {"torch": torch, "moss_engine": SimpleNamespace(Moss=constructor)}):
            worker.synth_child(conn, self.cfg)
        constructor.assert_called_once_with(
            **{name: self.cfg["moss"][name] for name in ("model", "codec", "refs")}, ffmpeg=self.cfg["ffmpeg"])
        empty_cache.assert_called_once()
        self.assertEqual([call.args[0][0] for call in conn.send.call_args_list], ["ready", "oom", "ok", "ok"])
        self.assertEqual(conn.send.call_args.args[0], ("ok", ([b"\x01\x00"], 24000)))


if __name__ == "__main__":
    unittest.main()
