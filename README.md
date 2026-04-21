# Original Project

The original project was called Game Glitch Investigator starter. The original goal of the project was to understand and fix the source code of a number guessing game. the fixed version of the game will correctly give hints to the user and the number in the system doesn't change. 

# Title

Smarter Guessing Game

# Summary

The project adds an agentic workflow to the game, able to watch over the game's state that can work against the user or offer coaching to help the user. 

# Architecture Overview

The diagram shows the process of the user playing the game, giving valid answers to move forward check_guess, then compares it to the secret number and updates the score. At the same time, the agent opponent cycles through a plan, act, reflect on every turn, planning a midpoint guess, committing it, and narrowing the guesses on the feedback that is run independently of the user. Everything is run on Streamlit UI to give the user feedback and recieve the next guess until the loop ends. 

# Setup Instructions



# Sample Interactions




# Design Decisions



# Testing Summary 



# Reflection


