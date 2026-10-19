import pytest
from assistant_core.tools import parse_credits, tuition
from assistant_core.errors import InvalidRequest

def test_parse_with_retake(): 
    assert parse_credits("tuition for 18 credits and 2 retake") == (18, 2) 
  
def test_tuition_value(): 
    assert tuition(18, 2, 450_000, 1.5, 30) == 9_450_000   # same as the monolith 
  
@pytest.mark.parametrize("credits", [0, 31]) 
def test_tuition_out_of_range(credits): 
    with pytest.raises(InvalidRequest): 
        tuition(credits, 0, 450_000, 1.5, 30) 

def test_parse_no_retake():
    assert parse_credits("fee for 18 credits") == (18, 0)

def test_parse_no_numbers_raises():
    with pytest.raises(InvalidRequest):
        parse_credits("how many credits?")

def test_tuition_lower_bound():
    assert tuition(1, 0, 450_000, 1.5, 30) == 450_000

def test_tuition_upper_bound():
    assert tuition(30, 0, 450_000, 1.5, 30) == 13_500_000

def test_tuition_no_retake():
    assert tuition(18, 0, 450_000, 1.5, 30) == 8_100_000