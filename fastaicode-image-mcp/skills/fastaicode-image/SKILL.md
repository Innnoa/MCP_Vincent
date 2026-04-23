---
name: fastaicode-image
description: Use when the user wants to generate an image through the local FastAICode MCP plugin, choose between 1k/2k/4k/auto presets, control local output paths, or troubleshoot FastAICode image generation errors.
---

# Fastaicode Image

## Overview

This skill standardizes how to use the local `generate_image` and `edit_image` MCP tools backed by the FastAICode-compatible image API. It is for image generation or image editing requests where Codex should pick sensible arguments, save the image locally, and return the saved file path instead of handling Base64 manually.

## Quick Start

Prefer the MCP tool `generate_image` whenever the user asks to create an image, render an illustration, produce a mockup, or save an AI-generated picture locally.
Prefer `edit_image` whenever the user says “基于这张图改”, “把这张图变成…”, “图生图”, or provides an existing local image to modify.

Default call shape:

```json
{
  "prompt": "user intent rewritten as a concrete image prompt",
  "size_preset": "auto"
}
```

Add `output_path` only when the user explicitly wants a specific file location. Otherwise let the tool save into the plugin default output directory.

Default edit call shape:

```json
{
  "prompt": "clear image editing instruction",
  "input_image_path": "/absolute/or/known/local/path/to/image.png",
  "size_preset": "auto"
}
```

## Presets

Use the preset names, not raw provider-specific pricing or dimension jargon:

- `1k`: standard square output, mapped by plugin config to a stable concrete size
- `2k`: service default or `auto` quality tier
- `4k`: only use when the caller explicitly asks for highest quality and the config defines it
- `auto`: preferred default when the user does not care about exact resolution

Do not silently downgrade `4k`. If the tool reports that `4k` is not configured, surface that error back to the user.
The plugin now has a `4k` mapping configured, but it is never used by default. Only send `4k` if the caller explicitly passes `size_preset: "4k"`.

## Output Rules

- Default save location comes from plugin config and should normally be used as-is.
- When the user asks for a specific folder or file name, pass `output_path`.
- If the user only wants a readable file name, prefer `filename_hint` and let the tool choose the directory.
- Always report the returned `saved_path` back to the user.
- For `edit_image`, also report `source_image_path` back to the user when useful.

## Prompt Shaping

- Turn short user requests into direct visual prompts before calling the tool.
- Keep the prompt focused on visible content, style, composition, and background.
- Do not mention `b64_json`, decoding, or transport details in the prompt.
- For `edit_image`, describe the intended transformation, not the original transport details.

Example:

User asks: `画一个极简红点图标`
Call intent:

```json
{
  "prompt": "a minimal tiny red circle icon on a clean white background",
  "size_preset": "1k"
}
```

## Error Handling

If the tool returns `ok: false`:

- Surface `error_code` and `message` clearly.
- If the error mentions `FASTAICODE_API_KEY`, tell the user the local API key is missing.
- If the error mentions `data[0].b64_json`, treat it as an upstream response format problem.
- If the error is about `4k`, ask the user whether to re-run with `2k` or `1k`.
- If the error is `FileNotFoundError`, tell the user the local source image path is wrong or missing.

## Boundaries

- The MCP tools execute the network request, Base64 decoding, and file writing.
- This skill only standardizes when to call the tool and how to shape its arguments.
