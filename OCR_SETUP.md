# OCR-Based Statistics Extraction

## ✅ Implementation Complete!

The bot now uses **OCR (Optical Character Recognition)** to extract percentages directly from screenshots of the page. This is much more reliable than trying to parse HTML!

## How It Works:

1. **Takes Full Page Screenshot**: The bot captures the entire page as an image
2. **OCR Text Extraction**: Uses Tesseract OCR to read all text from the screenshot
3. **Percentage Detection**: Finds percentages (52%, 73%, etc.) in the OCR text
4. **Keyword Matching**: Matches percentages with keywords (JOGADOR/PLAYER, BANCA/BANKER, EMPATE/TIE)
5. **Statistics Extraction**: Returns player, banker, and tie percentages

## What Changed:

### ✅ Added OCR Functionality
- Uses `pytesseract` for OCR
- Takes full-page screenshots
- Extracts text from images
- Parses percentages intelligently

### ✅ Primary Method: OCR
- OCR extraction is now the **primary method**
- HTML/text extraction is the **fallback method**

### ✅ Smart Percentage Matching
- Looks for percentages near keywords
- Handles both Portuguese (JOGADOR, BANCA, EMPATE) and English (PLAYER, BANKER, TIE)
- Takes the largest percentage if multiple found

## Benefits:

1. **Works Regardless of HTML Structure**: Doesn't depend on specific HTML elements
2. **Reads Visual Content**: Gets exactly what you see on screen
3. **Handles Dynamic Content**: Works with JavaScript-rendered content
4. **More Reliable**: Less prone to breaking when website structure changes

## Requirements:

- ✅ `pytesseract` - Python wrapper for Tesseract
- ✅ `Pillow` - Image processing
- ✅ `Tesseract OCR` - Already installed on your system

## How to Use:

Just run the bot as usual:
```bash
python bot.py
```

The bot will:
1. Take a screenshot of the page
2. Extract percentages using OCR
3. Check if player percentage > 50%
4. Send Telegram alert if condition is met

## What to Expect:

When the bot runs, you'll see logs like:
```
Taking screenshot for OCR extraction...
Extracting text from screenshot using OCR...
Found 15 percentages in OCR text: ['52', '73', '40', '8', ...]
Found player percentage: 52% in line: JOGADOR 52%
✅ OCR extraction successful: Player=52%, Banker=40%, Tie=8%
```

## Troubleshooting:

If OCR doesn't work:
1. Make sure Tesseract OCR is installed
2. Check that the page has loaded completely (wait time is 10 seconds)
3. Check logs for OCR errors
4. The bot will fall back to HTML extraction if OCR fails

---

**Your approach is now implemented!** The bot captures the whole screen and reads percentages from it, then sends Telegram alerts when player percentage > 50%. 🎉

