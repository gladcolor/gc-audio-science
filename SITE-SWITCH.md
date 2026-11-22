# 网站切换朗读音频来源（给内容电脑）

**迁移状态：已完成**（2026-11-19 18:28）。227 课 + 共享句的旧 MP3 都已复制进三个音频仓库并推送。可以切换了。

请把网站的朗读音频切换到下面三个音频仓库。

## 怎么加载

- 按 `shared/audio-sources.js` 选仓库。
- 每课加载 `<repo url><subject>/<topic>/manifest.js`。
- 播放 `<repo url><subject>/<topic>/<lang>/<key>.mp3`。

## manifest 格式

新 manifest 是**每课一个文件，两种语言写在一起**。旧的是每种语言一个文件，格式不一样：

```js
LabAudioManifest({"lesson": "biology/cell-theory", "voice": "serena", "en": "<key> <key> …", "zh": "<key> …"})
```

- 扩展名固定是 `mp3`。
- `voice` 现在总是 `"serena"`。还没重录的课，有些句子还是旧声音的 MP3（迁移过来的），但文件路径一样。
- manifest 里没列出的句子没有录音，页面照旧用浏览器朗读。

## 共享句

地方书的共享句在 `gc-audio-humanities/_shared/manifest.js`。仓库里有 `.nojekyll`，所以 `_shared/` 可以正常访问。

## 例子

- manifest：https://gladcolor.github.io/gc-audio-science/biology/cell-theory/manifest.js
- 一条录音：https://gladcolor.github.io/gc-audio-science/biology/cell-theory/en/02225020.mp3

## 顺序

1. 改 `lab.js`，从音频仓库加载。
2. 在页面上确认能播放。
3. 再从网站删除 `audio/`。

每个仓库的进度在 `status/STATUS.md`（例如 https://github.com/gladcolor/gc-audio-science/blob/main/status/STATUS.md）。
