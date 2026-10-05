from pydantic import BaseModel, Field
#Pydantic used to define structured Python data.


 #one customer support email entering our system eg.:SupportEmail(text="My account is locked.")
class SupportEmail(BaseModel):
    text: str = Field(min_length=1) #email cannot be empty


#what llm classifies it as, eg: billing, technical, general, account
class ClassificationResult(BaseModel): 
    category: str
    summary: str


#represents a single evaluation case for testing the llm's classification and summarization capabilities
class EvaluationCase(BaseModel):
    id: str
    input: SupportEmail
    expected_category: str
    expected_summary: str
    difficulty: str
    notes: str = ""