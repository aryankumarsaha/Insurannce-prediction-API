# add= lambda a,ab: a+ab
# subtract= lambda a,ab: a-ab

# print(add(5,3))
# print(subtract(5,3))

import pandas as pd

data = [10,20,30,40]
df = pd.DataFrame(data)
print(df)

def load_data():
    with open('data.csv', 'r') as f:
        data = f.read()


