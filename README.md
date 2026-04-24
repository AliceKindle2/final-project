# Original Project

The original project was called Game Glitch Investigator starter. The original goal of the project was to understand and fix the source code of a number guessing game. the fixed version of the game will correctly give hints to the user and the number in the system doesn't change. 

# Title

Smarter Guessing Game

# Summary

The project adds an agentic workflow to the game, able to watch over the game's state that can work against the user or offer coaching to help the user. 

# Architecture Overview

The diagram shows the process of the user playing the game, giving valid answers to move forward check_guess, then compares it to the secret number and updates the score. At the same time, the agent opponent cycles through a plan, act, reflect on every turn, planning a midpoint guess, committing it, and narrowing the guesses on the feedback that is run independently of the user. Everything is run on Streamlit UI to give the user feedback and recieve the next guess until the loop ends. 

# Setup Instructions

1. Make sure python and streamlit are installed on the device.
2. Have both files in the same folder and navigate to the folder using cd.
3. Run the app using streamlit run app.py.
6. Play the game by chose the difficulty, toggle the AI opponent on or off, and then guess.


# Sample Interactions

There are no ways to show the user and the AI intereacting due to them both working indepencently to produce the right answer, but the AI is influenced when the uesr enters in their own answer to move forward with the next guess and take input from the system to guess higher or lower. 

# Design Decisions

The core design of the agent is supposed to be fully independent from the user due to it's role as a competitor to the user. It is built to plan, act, and reflect on its actions, using binary search to do so. The trade off due to the binary search, the competition feels hollow due to the user and AI running differently along with AI not stressed due to focusing on binary search. 

# Testing Summary 

I tested the AI by using six different pytest. After some trial and error, the AI passed all pytests, showing that AI works well in the enivorment even when there is no user to interact with it. I learned that AI consistently works better in an idenpendent spaces, while might not being correct, it isn't stressed by taking user's prompt into consideration.

I also tested the AI via human evalution by playing the guessing game against the AI ten times. The AI was very consistent in it's predictions in the guessing game, taking the same steps in each game after given the hints, and overall consistent in it's predictions.

# Reflection

After creating an AI agent, I have a better understanding how AI works and the best way to implement. AI working independent spaces and given a thorough structure to follow is lessed stressed than it would be if it was basing its guesses with considering the users guesses. Also it's very easy for an AI to efficient if it follows a strict system like binary search to lead it to the right answer. 

If I had more time, I would develop the AI to the user's guesses into consideration so it could have more chances to be tested and become stressed due to the user potentially misleading it 

## Demo Walkthrough
https://www.loom.com/share/5c0659417963432a8c8f3205f3542b7d
https://github.com/AliceKindle2/final-project

This project shows I can fully implement an AI to a fully functional code and make a fun competition against the user while it uses a binary search algorithm to stay on top of the guessing game. 