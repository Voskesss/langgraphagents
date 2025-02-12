import sys
import os

# Voeg de project root toe aan Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.web_tools import search_web

def test_search():
    query = "InFacilities organisatie geschiedenis wanneer actief"
    print(f"Zoeken naar: {query}")
    results = search_web(query)
    print("\nResultaten:")
    print(results)

if __name__ == "__main__":
    test_search()
