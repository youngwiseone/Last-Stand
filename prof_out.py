# Step 1: Run the code with cProfile
# py -m cProfile -o prof.out main.py
# Step 2: Analyze the profile data
# py prof_out.py

import pstats
st = pstats.Stats('prof.out')
st.strip_dirs().sort_stats('tottime')

# collect only entries where tottime > 0.0
rows = [(func, data) for func, data in st.stats.items() if data[2] > 0]
# st.stats[func] → (cc, nc, tottime, cumtime, callers)

# sort again because we just built a new list
rows.sort(key=lambda t: t[1][2], reverse=True)

print(f'Function name                                 ncalls   tottime')
print('-'*65)
for func, data in rows[:10]:                   # top-10
    ncalls = data[1]
    tottime = data[2]
    print(f'{func[2]:<45} {ncalls:>7}   {tottime:8.6f}')
