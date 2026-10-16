# WikiGPT
[![Release](https://img.shields.io/github/v/release/DanDevProjects/wikigpt?style=flat-square)](https://github.com/DanDevProjects/Internet_Explorative/releases)
[![Downloads](https://img.shields.io/github/downloads/DanDevProjects/wikigpt/total?style=flat-square)](https://github.com/DanDevProjects/Internet_Explorative/releases)
[![Stars](https://img.shields.io/github/stars/DanDevProjects/wikigpt?style=flat-square)](https://github.com/DanDevProjects/Internet_Explorative/stargazers)
[![License](https://img.shields.io/github/license/DanDevProjects/wikigpt?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.14%2B-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)

## About WikiGPT
WikiGPT is a CLI-first and API based AI assistant that grounds its answers in real Wikipedia articles before speaking—synthesizing multiple articles, and falling back to native mode when Wikipedia doesn't have the answer.

> This is also my second "AI VS code" experiment. This time its Gemini 3.8 Flash VS WikiGPT!
---

## Why WikiGPT?

Large Language Models (LLMs) can sound confident even when they make things up.  Wikipedia often has more real info than sources such as Reddit, as its **not** a social media.
 **WikiGPT** solves this by putting Wikipedia first:

1. Whenever you ask a factual or explanatory question, WikiGPT extracts key topics and searches Wikipedia.
2. It fetches and reads **multiple relevant articles** simultaneously.
3. It synthesizes the information into a clear, cited answer.
4. If Wikipedia doesn't have an article (or you're just making small talk), it automatically tags the response:
   ```text
   [cannot find Wikipedia info, returning to native gpt mode]
and gives you the native Gemini response.
   
WikiGPT is also completely free, no payments for features, though there is usage limits, **depending on your API key type**. If its the free tier type, you can have access to a few million tokens.

## Gemini VS ChatGPT API

I chose Gemini 3.5 Flash-Lite because its completely **free**, efficient, uses less tokens and most people already have a Google account, which makes getting a key extremely easy. You might even be browsing on Google's Browser!

### How to get your API Key via Google Ai Studio

**Step 1**: Navigate to https://aistudio.google.com and log in.

**Step 2**: Go to the API keys section and click on "create API key".

**Step 3**: Run export GEMINI_API_KEY="YOUR_API_KEY" on Linux or macOS. If you are on Windows, use the set GEMINI_API_KEY="YOUR_API_KEY" command.

## How to use WikiGPT CLI

**For beginners**, Simply **Install Python** from the official HomePage, run the **wikigpt** command (macOS/Linux) or **python3 wikigpt.py** (Windows/macOS/Linux).

**For Advanced users/ Troubleshooters**, do whatever you want, edit the code, add more features, or anything. Run by using the universal command.

## Unlock more features by editing

You can unlock Gemini 3.5 Flash or even the latest models by editing the main code. You can do this by going into wikigpt.py, find the model names, edit them and run it. This might effect usage of models on free tier, but if you have paid for Ai Studio, this is your best choice.

## Demo of appearance

  ```text
  ===========================================================================
    Welcome To WikiGPT!                                                     |
  WikiGPT is based on Google Gemini.                                        |
  Made with ❤️  By DanDevProjects!                                          |
  See more of my projects at https://github.com/dandevprojects .            |
  note: AI can make mistakes.                                               |
  WikiGPT version 1.0.0 (Gemini 3.5)                                        |
  Don't forget to export your API key everytime you restart your computer.  |
  =========================================================================
  
  Ready! 

  WikiGPT> Hello!
  
  Thinking and searching Wikipedia...
  
  [cannot find Wikipedia info, returning to native gpt mode]
  
  Hello! How can I help you today?
  
  ------------------------------------------------------------
  WikiGPT>
```
As you can see, when the model cannot find any info from Wikipedia, it will automatically transition to native mode that only uses its own memory.

## Support for Windows

Support for Windows more different than macOS and Linux. You will need to install Python 3.9 or later and errors might be different. So, using this on a Mac or a Linux PC is better as it doesn't have that much bugs and is sometimes more stable.

## Commands

- exit or quit: Quit the command\
- /history: list the previous messages and responses
- /help: list commands
- /clear: clear history

## Chat

You can simply just type as usual like a normal Ai chat. I chose CLI because its **lightweight, works on almost any system, and require almost no setup.**

WikiGPT is sometimes fast, sometimes slow, speed depends on your API key and your computer. Normal responses takes approx. less than 15 Seconds.

## Installation

### To install on macOS/ Linux:
Run this command in the terminal inside of the directory where the code, the installer and the instructions file live:

```bash
./install.sh
```
### To install on Windows:
**No Setup**. You can just double click the .py file.

**IMPORTANT**: Remember to export your API key every time you restart your computer.

Run this (macOS/ Linux):
```bash
export GEMINI_API_KEY="Your api key"
```
Or this (Windows)
```bash
set GEMINI_API_KEY="Your api key"
```
Then run the script.

## License
This project uses the MIT License. See the License at LICENSE.md

Thank You for using WikiGPT. To report issues, you can report it on our discussions page or bug report file.
