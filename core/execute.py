import pyautogui
import time
import json
import random
import math
import threading
import keyboard
import sys

pyautogui.useImageNotFoundException(False)

from core.state import check_support_card, check_failure, check_turn, check_mood, check_current_year, check_criteria
from core.logic import do_something
from utils.constants import MOOD_LIST
from core.recognizer import is_infirmary_active, match_template
from utils.scenario import ura

paused = False

def toggle_pause():
    global paused
    paused = not paused
    print(f"[INFO] {'Paused' if paused else 'Resumed'} (Ctrl+Shift+Q)")

def listen_for_hotkeys():
    keyboard.add_hotkey('ctrl+shift+q', toggle_pause)

with open("config.json", "r", encoding="utf-8") as file:
  config = json.load(file)

MINIMUM_MOOD = config["minimum_mood"]
PRIORITIZE_G1_RACE = config["prioritize_g1_race"]

# ─── Utility Functions ─────────────────────────────────────────────────────────
def random_delay(min_delay=0.2, max_delay=0.7):
    time.sleep(random.uniform(min_delay, max_delay))
    
def wiggle_cursor(times=2, distance=2):
    for _ in range(times):
        dx = random.randint(-distance, distance)
        dy = random.randint(-distance, distance)
        pyautogui.moveRel(dx, dy, duration=random.uniform(0.03, 0.07))
        
def move_to_random(region):
    """Move mouse to a random point inside region using smooth tween."""
    x = random.randint(3, region.width - 3) + region.left
    y = random.randint(3, region.height - 3) + region.top

    tweens = [
        pyautogui.easeInOutQuad,
        pyautogui.easeOutQuad,
        pyautogui.easeInQuad,
        pyautogui.linear
    ]

    pyautogui.moveTo(x, y, duration=random.uniform(0.2, 0.5), tween=random.choice(tweens))
    wiggle_cursor()  # small human-like jitter at the end
    
def click(img, confidence = 0.8, minSearch = 2, click = 1, text = ""):
  if isinstance(img, str):
    btn = pyautogui.locateOnScreen(img, confidence=confidence, minSearchTime=minSearch)
  else:
    btn = img  # already a region (Box)
    
  if btn:
    if text:
      print(text)
    move_to_random(btn)
    time.sleep(0.2)
    pyautogui.click()
    time.sleep(0.2)
    return True
  
  return False

def go_to_training():
  return click("assets/buttons/training_btn.png")

def check_training():
  training_types = {
    "spd": "assets/icons/train_spd.png",
    "sta": "assets/icons/train_sta.png",
    "pwr": "assets/icons/train_pwr.png",
    "guts": "assets/icons/train_guts.png",
    "wit": "assets/icons/train_wit.png"
  }
  results = {}

  for key, icon_path in training_types.items():
    pos = pyautogui.locateOnScreen(icon_path, confidence=0.8)
    if pos:
      move_to_random(pos)
      pyautogui.mouseDown()
      support_counts = check_support_card()
      total_support = sum(support_counts.values())
      failure_chance = check_failure()
      results[key] = {
        "support": support_counts,
        "total_support": total_support,
        "failure": failure_chance
      }
      print(f"[{key.upper()}] → {support_counts}, Fail: {failure_chance}%")
      random_delay()
  
  pyautogui.mouseUp()
  return results

def do_train(train):
  train_btn = pyautogui.locateOnScreen(f"assets/icons/train_{train}.png", confidence=0.8)
  if train_btn:
    move_to_random(train_btn)
    pyautogui.tripleClick(train_btn, interval=0.1, duration=0.2)
    random_delay()

def do_rest():
  btn = pyautogui.locateOnScreen("assets/buttons/rest_btn.png", confidence=0.8)
  summer_btn = pyautogui.locateOnScreen("assets/buttons/rest_summer_btn.png", confidence=0.8)

  if btn:
    click(btn)
  elif summer_btn:
    click(summer_btn)

def do_recreation():
  btn = pyautogui.locateOnScreen("assets/buttons/recreation_btn.png", confidence=0.8)
  summer_btn = pyautogui.locateOnScreen("assets/buttons/rest_summer_btn.png", confidence=0.8)

  if btn:
    click(btn)
  elif summer_btn:
    click(summer_btn)

def do_race(prioritize_g1 = False):
  click(img="assets/buttons/races_btn.png", minSearch=10)
  click(img="assets/buttons/ok_btn.png", minSearch=0.7)

  found = race_select(prioritize_g1=prioritize_g1)
  if not found:
    print("[INFO] No race found.")
    return False

  race_prep()
  time.sleep(1)
  random_delay()
  after_race()
  return True

def race_day():
  click(img="assets/buttons/race_day_btn.png", minSearch=10)
  click(img="assets/buttons/ok_btn.png", minSearch=0.7)
  time.sleep(0.5)
  random_delay()

  for i in range(2):
    click(img="assets/buttons/race_btn.png", minSearch=2)
    time.sleep(0.5)

  race_prep()
  time.sleep(1)
  random_delay()
  after_race()

def race_select(prioritize_g1 = False):
  move_to_random(x=560, y=680)

  time.sleep(0.2)
  random_delay()

  if prioritize_g1:
    print("[INFO] Looking for G1 race.")
    for i in range(2):
      race_card = match_template("assets/ui/g1_race.png", threshold=0.9)

      if race_card:
        for x, y, w, h in race_card:
          region = (x, y, 310, 90)
          match_aptitude = pyautogui.locateOnScreen("assets/ui/match_track.png", confidence=0.8, minSearchTime=0.7, region=region)
          if match_aptitude:
            print("[INFO] G1 race found.")
            click(match_aptitude, duration=0.2)
            for i in range(2):
              race_btn = pyautogui.locateOnScreen("assets/buttons/race_btn.png", confidence=0.8, minSearchTime=2)
              if race_btn:
                click(race_btn)
                time.sleep(0.5)
                random_delay()
            return True
      
      for i in range(4):
        pyautogui.scroll(-300)
    
    return False
  else:
    print("[INFO] Looking for race.")
    for i in range(4):
      match_aptitude = pyautogui.locateOnScreen("assets/ui/match_track.png", confidence=0.8, minSearchTime=0.7)
      if match_aptitude:
        print("[INFO] Race found.")
        click(match_aptitude)

        for i in range(2):
          race_btn = pyautogui.locateOnScreen("assets/buttons/race_btn.png", confidence=0.8, minSearchTime=2)
          if race_btn:
            click(race_btn)
            time.sleep(0.5)
            random_delay()
        return True
      
      for i in range(4):
        pyautogui.scroll(-300)
    
    return False

def race_prep():
  view_result_btn = pyautogui.locateOnScreen("assets/buttons/view_results.png", confidence=0.8, minSearchTime=20)
  if view_result_btn:
    click(view_result_btn)
    time.sleep(0.5)
    random_delay()
    for i in range(3):
      pyautogui.tripleClick(interval=0.2)
      time.sleep(0.5)
      random_delay()

def after_race():
    # Click the first "Next" button
    click(img="assets/buttons/next_btn.png", minSearch=5)
    time.sleep(0.5)
    random_delay()
    pyautogui.click()
    random_delay()

    # Wait for the first appearance of "Next2" button with a timeout loop
    print("[INFO] Waiting for NEXT2 button to appear...")
    next2_btn = None
    timeout = time.time() + 15  # up to 15 seconds
    while time.time() < timeout:
        next2_btn = pyautogui.locateOnScreen("assets/buttons/next2_btn.png", confidence=0.8)
        if next2_btn:
            break
        time.sleep(0.5)

    if next2_btn:
        click("assets/buttons/next2_btn.png", minSearch=1)
        time.sleep(0.5)
        random_delay()

  
threading.Thread(target=listen_for_hotkeys, daemon=True).start()

def career_lobby():
  try:
    # Program start
    while True:
      if paused:
        print("[INFO] Paused. Waiting... (Ctrl+Shift+Q to resume)")
        while paused:
          time.sleep(0.5)
        print("[INFO] Resumed.")
  
      # First check, event
      if click(img="assets/icons/event_choice_1.png", minSearch=0.2, text="[INFO] Event found, automatically select top choice."):
        continue

      # Second check, inspiration
      if click(img="assets/buttons/inspiration_btn.png", minSearch=0.2, text="[INFO] Inspiration found."):
        continue
        
      # Third check, next
      if click(img="assets/buttons/next_btn.png", minSearch=0.2):
        continue
        
      # Fourth check, cancel
      if click(img="assets/buttons/cancel_btn.png", minSearch=0.2):
        continue

      # Check if current menu is in career lobby
      tazuna_hint = pyautogui.locateOnScreen("assets/ui/tazuna_hint.png", confidence=0.8, minSearchTime=0.2)
      if tazuna_hint is None:
        print("[INFO] Should be in career lobby.")
        continue

      time.sleep(0.5)
      random_delay()

      # Check if there is debuff status
      debuffed = pyautogui.locateOnScreen("assets/buttons/infirmary_btn2.png", confidence=0.9, minSearchTime=1)
      if debuffed:
        if is_infirmary_active((debuffed.left, debuffed.top, debuffed.width, debuffed.height)):
          click(debuffed)
          print("[INFO] Character has debuff, go to infirmary instead.")
          continue

      mood = check_mood()
      mood_index = MOOD_LIST.index(mood)
      minimum_mood = MOOD_LIST.index(MINIMUM_MOOD)
      turn = check_turn()
      year = check_current_year()
      criteria = check_criteria()
      
      print("\n=======================================================================================\n")
      print(f"Year: {year}")
      print(f"Mood: {mood}")
      print(f"Turn: {turn}\n")

      # URA SCENARIO
      if year == "Finale Season" and turn == "Race Day":
        print("[INFO] URA Finale")
        ura()
        for i in range(2):
          if click(img="assets/buttons/race_btn.png", minSearch=2):
            time.sleep(0.5)
            random_delay()
        
        race_prep()
        time.sleep(1)
        after_race()
        continue

      # If calendar is race day, do race
      if turn == "Race Day" and year != "Finale Season":
        print("[INFO] Race Day.")
        race_day()
        continue

      # Mood check
      if mood_index < minimum_mood:
        print("[INFO] Mood is low, trying recreation to increase mood")
        do_recreation()
        continue

      # Check if goals is not met criteria AND it is not Pre-Debut AND turn is less than 10 AND Goal is already achieved
      if criteria.split(" ")[0] != "criteria" and year != "Junior Year Pre-Debut" and turn < 10 and criteria != "Goal Achievedl":
        race_found = do_race()
        if race_found:
          continue
        else:
          # If there is no race matching to aptitude, go back and do training instead
          click(img="assets/buttons/back_btn.png", text="[INFO] Race not found. Proceeding to training.")
          time.sleep(0.5)

      year_parts = year.split(" ")
      # If Prioritize G1 Race is true, check G1 race every turn
      if PRIORITIZE_G1_RACE and year_parts[0] != "Junior" and len(year_parts) > 3 and year_parts[3] not in ["Jul", "Aug"]:
        g1_race_found = do_race(PRIORITIZE_G1_RACE)
        if g1_race_found:
          continue
        else:
          # If there is no G1 race, go back and do training
          click(img="assets/buttons/back_btn.png", text="[INFO] G1 race not found. Proceeding to training.")
          time.sleep(0.5)
      
      # Check training button
      if not go_to_training():
        print("[INFO] Training button is not found.")
        continue

      # Last, do training
      time.sleep(0.5)
      random_delay()
      results_training = check_training()
      best_training = do_something(results_training)
      if best_training:
        do_train(best_training)
      else:
        # If not training, go back first before doing rest
        click(img="assets/buttons/back_btn.png", text="[INFO] No good training. Returning to rest.")
        time.sleep(0.5)
        random_delay()
        do_rest()
        random_delay()

  except KeyboardInterrupt:
    print("\n[INFO] Ctrl+C detected inside career_lobby. Exiting.")
    sys.exit(0)
