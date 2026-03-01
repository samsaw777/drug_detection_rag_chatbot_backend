"""
Adds the project root to Python's module search path so that
test files can import project modules (schemas, services, routes) directly.
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))