# HARDBRUT → Android Adaptation Guide

## Philosophy

HARDBRUT on Android follows the same rules as on the web:
- Zero border-radius (unless a shape demands it — radios are circles, that's fine)
- Hard shadows (elevation in Compose = no blur, just offset)
- Two button kinds (default yellow, cancel white)
- Every interactive element carries its shadow at all times
- Typography: bold, uppercase labels, Impact-like display face

## Token mapping

| CSS token      | CSS value                    | Android equivalent                    |
|----------------|------------------------------|---------------------------------------|
| --ink          | #000000                      | Color(0xFF000000)                     |
| --paper        | #FFFFFF                      | Color(0xFFFFFFFF)                     |
| --bg           | #fdfaf2                      | Color(0xFFFDFAF2)                     |
| --yellow       | #ffd23f                      | Color(0xFFFFD23F)                     |
| --muted        | #666666                      | Color(0xFF666666)                     |
| --border       | 3px solid #000               | BorderStroke(3.dp, Color.Black)       |
| --shadow       | 5px 5px 0 #000 (no blur)     | Modifier.shadow(5.dp, offset=5,5)     |
| --shadow-sm    | 3px 3px 0 #000               | Modifier.shadow(3.dp, offset=3,3)     |
| --shadow-lg    | 7px 7px 0 #000               | Modifier.shadow(7.dp, offset=7,7)     |
| --space        | 1.5rem (~24dp)               | 24.dp                                 |
| --space-sm     | 0.75rem (~12dp)              | 12.dp                                 |
| --space-lg     | 2.5rem (~40dp)               | 40.dp                                 |

**CRITICAL**: Android's `Modifier.shadow()` does NOT support zero blur radius.
The minimum blur is ~1dp. This is acceptable — the spirit is preserved.
If you need true hard shadows with zero blur, draw a `Box` behind the element
with `Modifier.offset(x, y)` and the shadow color.

## Typography

```kotlin
// Use a bold, condensed, uppercase display face.
// System fonts that work: "sans-serif-black" on newer Androids.
// For a custom equivalent of Impact, bundle a font like Anton or Bebas Neue.

val DisplayFont = FontFamily(
    Font(R.font.anton, FontWeight.Bold) // or sans-serif-black
)

// Heading style: uppercase, tight spacing, Impact-like
val HeadingStyle = TextStyle(
    fontFamily = DisplayFont,
    fontWeight = FontWeight.Bold,
    textTransform = TextTransform.Uppercase,
    letterSpacing = (-0.5).sp,
    lineHeight = 1.1.em
)

// Body: system sans-serif, normal case
val BodyStyle = TextStyle(
    fontFamily = FontFamily.SansSerif,
    fontSize = 17.sp,
    lineHeight = 28.sp
)

// Muted text
val MutedStyle = BodyStyle.copy(color = Color(0xFF666666))

// Mono (for badges, code)
val MonoStyle = TextStyle(
    fontFamily = FontFamily.Monospace,
    fontSize = 12.sp,
    textTransform = TextTransform.Uppercase,
    letterSpacing = 0.6.sp
)
```

## Buttons

Two kinds only. Same size, same border, same animation. Only `background` and `shadow-size` differ.

```kotlin
@Composable
fun HardbrutButton(
    onClick: () -> Unit,
    kind: ButtonKind = ButtonKind.Default,
    enabled: Boolean = true,
    content: @Composable RowScope.() -> Unit
) {
    val shadowSize = when (kind) {
        ButtonKind.Default -> 5.dp
        ButtonKind.Cancel -> 3.dp
    }
    val bg = when (kind) {
        ButtonKind.Default -> Color(0xFFFFD23F)  // yellow
        ButtonKind.Cancel -> Color.White
    }

    Box(
        modifier = Modifier
            .shadow(shadowSize, offset = Offset(shadowSize, shadowSize))
            .border(3.dp, Color.Black)
            .background(bg)
            .clickable(enabled = enabled) { onClick() }
            .padding(horizontal = 24.dp, vertical = 12.dp),
        contentAlignment = Alignment.Center
    ) {
        Row(horizontalArrangement = Arrangement.Center, verticalAlignment = Alignment.CenterVertically) {
            content()
        }
    }
}

enum class ButtonKind { Default, Cancel }
```

**Interaction**: HARDBRUT buttons do NOT animate on press like the web version (no translate-in).
Android handles the press feedback via ripple (the default) — set ripple color to `Color.Black.copy(alpha = 0.15f)`.

## Cards

```kotlin
@Composable
fun HardbrutCard(
    modifier: Modifier = Modifier,
    content: @Composable ColumnScope.() -> Unit
) {
    Column(
        modifier = modifier
            .shadow(5.dp, offset = Offset(5.dp, 5.dp), clip = false)
            .border(3.dp, Color.Black)
            .background(Color.White)
            .padding(24.dp)
    ) { content() }
}
```

## Inputs (text fields)

```kotlin
// Always has shadow. Focus gets heavier shadow (3dp → 5dp).
@Composable
fun HardbrutTextField(
    value: String,
    onValueChange: (String) -> Unit,
    modifier: Modifier = Modifier,
    placeholder: String = "",
    label: String = ""
) {
    var focused by remember { mutableStateOf(false) }
    val shadowDp = if (focused) 5.dp else 3.dp

    Column(modifier = modifier) {
        if (label.isNotEmpty()) {
            Text(label, style = LabelStyle)
        }
        Box(
            modifier = Modifier
                .shadow(shadowDp, offset = Offset(shadowDp, shadowDp))
                .border(3.dp, Color.Black)
                .background(Color.White)
        ) {
            BasicTextField(
                value = value,
                onValueChange = onValueChange,
                modifier = Modifier
                    .focusRequester(remember { FocusRequester() })
                    .onFocusChanged { focused = it.isFocused }
                    .padding(horizontal = 14.dp, vertical = 11.dp)
                    .heightIn(min = 46.dp),
                textStyle = BodyStyle,
                decorationBox = { inner ->
                    if (value.isEmpty()) Text(placeholder, style = MutedStyle)
                    inner()
                }
            )
        }
    }
}
```

## Checkbox & Radio

```kotlin
// Always has 3dp shadow. No interaction-only shadow.
@Composable
fun HardbrutCheckbox(
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit
) {
    Box(
        modifier = Modifier
            .size(22.dp)
            .shadow(3.dp, offset = Offset(3.dp, 3.dp))
            .border(3.dp, Color.Black)
            .background(Color.White)
            .clickable { onCheckedChange(!checked) },
        contentAlignment = Alignment.Center
    ) {
        if (checked) Text("✓", fontWeight = FontWeight.ExtraBold, fontSize = 14.sp)
    }
}

@Composable
fun HardbrutRadio(
    selected: Boolean,
    onClick: () -> Unit
) {
    Box(
        modifier = Modifier
            .size(22.dp)
            .shadow(3.dp, offset = Offset(3.dp, 3.dp))
            .border(3.dp, Color.Black)
            .background(Color.White, CircleShape)
            .clickable { onClick() },
        contentAlignment = Alignment.Center
    ) {
        if (selected) {
            Box(
                modifier = Modifier
                    .size(8.dp)
                    .background(Color.Black, CircleShape)
            )
        }
    }
}
```

## Badge

```kotlin
@Composable
fun HardbrutBadge(text: String) {
    Text(
        text = text.uppercase(),
        style = MonoStyle,
        modifier = Modifier
            .shadow(3.dp, offset = Offset(3.dp, 3.dp))
            .border(2.dp, Color.Black)
            .background(Color(0xFFFFD23F))
            .padding(horizontal = 10.dp, vertical = 3.dp)
    )
}
```

## Details (expandable)

```kotlin
// Compose doesn't have <details> — use AnimatedVisibility
@Composable
fun HardbrutDetails(
    summary: String,
    expanded: Boolean,
    onToggle: () -> Unit,
    content: @Composable () -> Unit
) {
    val shadowDp = if (expanded) 5.dp else 3.dp
    Column(
        modifier = Modifier
            .shadow(shadowDp, offset = Offset(shadowDp, shadowDp))
            .border(3.dp, Color.Black)
            .background(Color.White)
    ) {
        Row(
            modifier = Modifier
                .clickable { onToggle() }
                .padding(horizontal = 24.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(if (expanded) "−" else "+", style = MonoStyle)
            Spacer(Modifier.width(8.dp))
            Text(
                summary.uppercase(),
                style = HeadingStyle.copy(fontSize = 15.sp)
            )
        }
        AnimatedVisibility(expanded) {
            Column(modifier = Modifier.padding(24.dp)) { content() }
        }
    }
}
```

## Callout

```kotlin
@Composable
fun HardbrutCallout(text: String) {
    Text(
        text = text,
        fontWeight = FontWeight.Bold,
        modifier = Modifier
            .shadow(3.dp, offset = Offset(3.dp, 3.dp))
            .border(3.dp, Color.Black)
            .background(Color(0xFFFFD23F))
            .padding(24.dp)
    )
}
```

## Shadow helper (zero-blur workaround)

Android `Modifier.shadow()` doesn't do zero-blur. If you need perfectly hard shadows,
use this composable instead (draws a colored rect behind the element):

```kotlin
fun Modifier.hardShadow(size: Dp, color: Color = Color.Black): Modifier = this.then(
    drawBehind {
        drawRect(
            color = color,
            topLeft = Offset(size.toPx(), size.toPx()),
            size = Size(this.size.width, this.size.height)
        )
    }
)
```

Use: `.hardShadow(5.dp)` instead of `.shadow(5.dp, offset = Offset(5.dp, 5.dp))`.

## Consistent spacing

All outer spacing uses multiples of `--space` (24dp). Internal padding inside
elements is `--space` (24dp). Tighter internal padding is `--space-sm` (12dp).

Do not add arbitrary padding values. Every `padding`, `margin`, and `gap` must
be one of: 12dp (tight), 24dp (normal), 40dp (wide).

## What to skip

- **Navbar**: use Material3 TopAppBar with custom colors. Or build a custom one
  with the same 4px bottom border and sticky behavior.
- **Grid**: use `LazyVerticalGrid` or `Row`/`Column` with weights.
- **Hero / Footer**: full-width bands with 4px border — trivial Column composition.
- **Message**: same as Callout but with smaller padding (12dp, 24dp).
- **Table**: use `LazyColumn` with `Row` items. The alternating row colors and
  2px internal borders are the key styling.
