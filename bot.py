SYSTEM_PROMPT = '''This is a simplified prompt for creating study materials that make complex topics easy to understand.'''  


def build_generation_prompt(next_topic):  
    return f"Let's explore {next_topic} and break it down for effective learning."  

PART_I = '''THE CONCEPT:  
Hinglish Explanation:  
Yeh ek concept hai jisse aap asaani se samajh sakte hain. Iska maqsad yeh hai ki aapko basics se lekar advanced level update karna.'''  

PART_II = '''EXAM INSIGHT:  
Historical Question Data:  
Pichle exams mein aane wale sawalon ka analysis yeh hai ki kaise yeh topic aapko samajh kar preparation mein madad karega.'''  

PART_III = '''THE DAILY BATTLE:  
MCQs:  
1. Sawal 1: Aapka pehla prashn hai?  
   A. Jawab A  
   B. Jawab B  
   C. Jawab C  
   D. Jawab D  

2. Sawal 2: Aapka doosra prashn hai?  
   A. Jawab A  
   B. Jawab B  
   C. Jawab C  
   D. Jawab D'''  

PART_IV = '''QUICK REVISION:  
Bullet Points:  
- Important concept  
- Key takeaway  
- Revision tips  
- Practice examples'''  

# Combine all parts into final content  
final_content = f"{SYSTEM_PROMPT}\n\n{build_generation_prompt('next topic')}\n\n" + PART_I + f"\n\n" + PART_II + f"\n\n" + PART_III + f"\n\n" + PART_IV