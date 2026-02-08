# Mishmash Icons

Minimalist outline icons for Email, Instagram, LinkedIn, and Discord.

## Files
- SVG icons: `assets/icons/svg/*.svg`
- PNG icons (16/24/32/48 px): `assets/icons/png/<size>px/*_<size>.png`
- SVG sprite: `assets/sprite/icons-sprite.svg`
- PNG sprite masks (@1x=24, @2x=48):
  - `assets/sprite/icons-sprite-mask@24.png`
  - `assets/sprite/icons-sprite-mask@48.png`
- CSS: `assets/css/icons.css`

## Usage
### Inline SVG from sprite (recommended)
```html
<link rel="stylesheet" href="assets/css/icons.css">
<svg class="icon" aria-hidden="true"><use href="assets/sprite/icons-sprite.svg#icon-email"></use></svg>
<svg class="icon" aria-hidden="true"><use href="assets/sprite/icons-sprite.svg#icon-instagram"></use></svg>
<svg class="icon" aria-hidden="true"><use href="assets/sprite/icons-sprite.svg#icon-linkedin"></use></svg>
<svg class="icon" aria-hidden="true"><use href="assets/sprite/icons-sprite.svg#icon-discord"></use></svg>
```

### PNG sprite via CSS mask (auto colors + hover)
```html
<link rel="stylesheet" href="assets/css/icons.css">
<i class="icon-png icon-png--email" aria-hidden="true"></i>
<i class="icon-png icon-png--instagram" aria-hidden="true"></i>
<i class="icon-png icon-png--linkedin" aria-hidden="true"></i>
<i class="icon-png icon-png--discord" aria-hidden="true"></i>
```

The base color and hover color follow your scheme:
- Default: dark `#363644` → hover purple `#A7A1F4`
- Dark mode (`prefers-color-scheme: dark`): default green `#C1F7AE` → hover purple `#A7A1F4`

You can override with CSS variables:
```css
:root { --icon-color: #222; --icon-hover-color: #8a2be2; }
```
