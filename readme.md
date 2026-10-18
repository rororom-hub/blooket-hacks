# Blooket CDP Farmer

### 1. Setup (One-Time)
  * `python -m venv .venv`
  * `.venv\Scripts\activate`
  * `pip install -e .`
  * Launch Chrome in debug mode (creates an isolated profile so you only log in once): `python cdp.py`


### 2. Usage (Daily)
p* In the opened Chrome window, start your quiz in **Solo -> Study** mode until the first question is on screen
* Run the farmer in your terminal:
  * `python script.py` *(clicks first answer box automatically 255 times)*
  * Or match specific answer text: `python script.py -t "1" -n 255`