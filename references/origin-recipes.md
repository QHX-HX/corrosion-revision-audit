# Origin recipes (verified against Origin 2024)

Automation channel: **PowerShell + COM** (`Origin.ApplicationSI`). No pywin32, no
`originpro` package needed. The bundled Python has neither, and Origin's COM is the
stable interface.

## Connect and disconnect

```powershell
$app = New-Object -ComObject Origin.ApplicationSI
$app.Visible = 0
...
$app.Exit()
```

Origin is a single-instance COM server. A second `New-Object` attaches to the running
instance instead of starting a new one, so always `Exit()` at the end (in a `finally`),
otherwise the licence seat stays held and the next run reuses a dirty project.

## What `Execute` and `Evaluate` actually return

- `Execute("labtalk;")` returns `True`/`False`, but **`True` does not mean it worked**.
  Several invalid commands return `True` and do nothing. Always verify by looking at the
  produced file or by `Evaluate`.
- `Evaluate("expression")` returns numbers only. **Strings come back as a sentinel**
  (`-1.23456789E-300`), and so do invalid expressions. Treat the sentinel as "no value".
  Useful checks: `wks.ncols`, `wks.nrows`, `layer.plot1.color`.

## Import

```
newbook name:="Fig1" sheet:=1;
impCSV fname:="C:/path/data.csv";
```

Works with forward slashes. Paths with Chinese characters or spaces are accepted, but
Origin may return an 8.3 short path in its own messages; do not compare strings.

## Data layout matters

`plotxy` needs **wide** data: `X1,Y1,X2,Y2,...`, one pair per curve. A tidy
(`x,y,group`) table must be pivoted first; `plot.ps1` does that.

## Plotting several curves

This is the form that works:

```
plotxy iy:=((1,2),(3,4),(5,6),(7,8)) plot:=202;
```

What does **not** work in 2024 via COM:

| Form | Result |
|---|---|
| `plotxy iy:=(1,2:5)` | rejected (only valid when all Y columns share one X) |
| `plotxy iy:=(1,2),(3,4)` | rejected |
| `layer -i202 [Book]1!4;` | returns True, adds nothing (graph not active) |

Plot codes: `200` line, `201` scatter, `202` line+symbol.

## Legend and column names

The legend text comes from the Y column long names:

```
wks.col2.lname$ = "191";
wks.col4.lname$ = "382";
legendupdate;
```

Set long names **before** `plotxy`; call `legendupdate` after plotting.

## Axis titles

```
xb.text$ = "Z' (\g(W)cm\+(2))";     // bottom X
yl.text$ = "-Z'' (\g(W)cm\+(2))";   // left Y
```

- Axis objects are `xb`, `xt`, `yl`, `yr`. **There is no `yb`** - using it silently does
  nothing and the Y title stays as the default column name.
- `\+(...)` = superscript, `\-(...)` = subscript, `\g(W)` = Ω.
- Do not nest `\+` inside `\-`; the parentheses get consumed and stray glyphs appear.
- `''` inside a double-quoted LabTalk string is a literal apostrophe; four of them
  (`''''`) produce two, which is how `-Z''` is written.

## Export

```
expGraph type:=png path:="C:/out/" filename:="fig" tr1:=1;
expGraph type:=tif path:="C:/out/" filename:="fig" tr1:=1;
```

- `tr1:=1` = transparent background for PNG.
- **`dpi:=600`, `tif.dpi:=600`, `png.dpi:=600` are all rejected** in 2024. Output
  resolution follows the graph page size (default page gives ~3200 x 2460 px).
- The command returns `True` even when it writes nothing (missing folder, invalid
  option). **Always check the file exists afterwards.**

## Page and layer geometry

`layer.width` / `layer.height` are **percentages of the page** (defaults ~68 / 72), not
centimetres. Combining `page.width = 16` with `layer.width = 10` collapsed the graph to a
small stamp in the corner. In practice: leave geometry alone, or build a template `.otp`
in the GUI and load it.

## Fonts, sizes and limits (verified properties)

| Property | Meaning | Status |
|---|---|---|
| `layer.x.label.pt` / `layer.y.label.pt` | axis **title** size in points (default 18) | verified, settable |
| `layer.x.label.font` / `layer.y.label.font` | font index (default 1; 2 = Times New Roman) | verified, settable |
| `layer.x.pt` / `layer.y.pt` | tick-label size | accepted |
| `layer.x.from` / `.to`, `layer.y.from` / `.to` | axis limits | verified, settable |
| `xb.font = "Times New Roman"` | accepted but reads back as an index | unreliable |
| `xb.pts`, `xb.size`, `xb.bold` | invalid | do not use |
| `layer.ratio` | invalid | do not use |

## Square Nyquist box

Equal axis limits are not enough: the plotting box is sized as a percentage of the
page, so a "square" box needs

```
height% = width% * page.width / page.height
```

On this install `page.width` = 6432 and `page.height` = 4923 (default A4 page), so
`width = 60` needs `height = 78.4`. `plot.ps1 -Square` computes this at run time and
also derives symmetric 0..max limits from the data.

`page.width = 16` is accepted but the value does not change, and combining it with a
small `layer.width` collapsed the figure to a corner stamp. Leave the page alone.

## Palette

Colour control through COM is **not viable** in Origin 2024. Evidence:

| Attempt | Result |
|---|---|
| `layer.plot1.color = 2` | returns True, read-back unchanged |
| `layer.plot1.color = color(0,0,255)` | returns True, read-back unchanged |
| `set %C -c 2;` | changes the *active* plot only |
| `layer -s 2;` (select plot 2) | returns False |
| `set [Book]1!4 -c 2;` | returns False |
| `set %C -c color(77,186,248)` | stores 16777216, not the RGB value |

Consequence: colours must be set once in the GUI and saved into the template.

## Handoff: build the skeleton, finish in the GUI

The practical workflow when a figure needs a custom palette:

1. `plot.ps1` (or a scripted session) builds the graph: data, curves, legend names,
   axis titles, square box, font index and sizes.
2. `$app.Save("C:/path/Fig10a.opju")` writes the project - this **does** work.
3. Open the `.opju` in Origin, set the four curve colours, move the legend off the frame,
   then `File > Save Template As` -> `house_style.otp`.
4. From then on `plot.ps1 -Template house_style.otp` reproduces the style automatically.

This is faster than fighting LabTalk: four colour picks replace dozens of failed
commands, and the template makes the result repeatable.

## Templates

`saveas type:=otp`, `save -t` and `doc -s` cannot write a template from LabTalk. Build
the template once in the GUI (File > Save Template As), save as `.otp`, then:

```powershell
plot.ps1 -Data d.csv -Out out -Name fig -Template C:\path\house_style.otp
```

The driver opens the template with `win -t plot "<tpl>"` and plots into it, so the
template carries font, palette, box shape and legend placement.

## What the driver still cannot fix

- Legend position: it defaults to the upper right and can overlap the frame. Move it
  once in the template.
- `-Z''` sometimes renders with a stray overbar because the two apostrophes are read as
  mark-up; using the Unicode double prime `″` avoids it.

## Recommended pattern

1. `probe.ps1` - confirm COM and version.
2. Build `house_style.otp` once in the GUI: TNR, square box, palette, legend inside.
3. `plot.ps1 -Template house_style.otp -Square ...` for every figure.
4. Export TIFF for submission, PNG for the response letter.
5. Open the result once: LabTalk rarely complains, it just does nothing.
