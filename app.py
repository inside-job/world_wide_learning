import streamlit as st

import pandas as pd
import numpy as np
from itertools import combinations
from st_aggrid import AgGrid
#st.set_page_config(layout="wide")

url = """https://docs.google.com/spreadsheets/d/1gd_SJn1AMJFXrfwIWglTfkImdNySX32zWGB0DYW4q4A/gviz/tq?tqx=out:csv&sheet=student_details"""
df = pd.read_csv(url).drop_duplicates(keep = 'first')

st.header('World Wide Learning')

st.subheader('Student Details')
AgGrid(df)

@st.cache
def convert_df(df):
    return df.to_csv().encode('utf-8')



if st.button('Group the batch'):
    df1 = df.groupby(['module','time_zone'], as_index=False)['student_id'].agg(lambda x: list(set(x)))
    df1.student_id = df1.student_id.apply(lambda x: [x[i:i + 6] for i in range(0, len(x), 6)] )
    df2 = pd.DataFrame(df1.student_id.values.tolist()).add_prefix('team_')
    df2['module'] = df1.module 
    df2['time_zone'] = df1.time_zone 
    first_column = df2.pop('module')
    df2.insert(0, 'module', first_column)
    first_column = df2.pop('time_zone')
    df2.insert(0, 'time_zone', first_column)

    df2.fillna("",inplace=True)
    for i in df2.columns:
        if 'team_' in i:
            df2[i] = [','.join(map(str, l)) for l in df2[i]]


    st.header('')

    st.subheader('Batching of student into teams')
    AgGrid(df2)
    
    csv = convert_df(df2)
    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name='large_df.csv',
        mime='text/csv')

    



#st.latex("Data")
st.header('')
st.header('')

st.markdown('Data Link') # df, err, func, keras!
# st.write(['st', 'is <', 3]) # see *
# st.title('My title')
# st.header('My header')
#st.subheader('Reference Data')
st.code("""https://docs.google.com/spreadsheets/d/1gd_SJn1AMJFXrfwIWglTfkImdNySX32zWGB0DYW4q4A/edit#gid=1633728087""")

# #schedule = pd.DataFrame(columns = ['student_id', 'time_zone']+[i for i in range(10, 18)])

# df[['utc_'+str(i) for i in range(10, 19)]] = [np.nan for i in range(10, 19)]
# for i in range(10, 19):
#     df['utc_'+str(i)] = df.utc_plus_time.apply(lambda x: 1 if 10<= i + x <=19 else 0)

# df = df[['student_id'] + ['utc_'+str(i) for i in range(10, 19)] ]    

# a = df.sum(axis = 0, skipna = True).to_frame()
# a['utc_time'] = a.index
# a.columns = ['count', 'utc_time']
# a = a[a.utc_time != 'student_id']
# a = a.sort_values(by='count', ascending=False)





# comb_rows = list(combinations(df.index, 6))

# combinations = pd.DataFrame([df.loc[c,:].sum() for c in comb_rows], index=comb_rows)

# combinations = pd.DataFrame([df.loc[c,:].sum() for c in comb_rows], index=comb_rows)





# data = [['Bread', 9, 'Food'], ['Shoes', 20, 'Clothes'], ['Shirt', 15, 'Clothes'], ['Milk', 5, 'Drink'], ['Cereal', 8, 'Food'], ['Chips', 10, 'Food'], ['Beer', 15, 'Drink'], ['Popcorn', 3, 'Food'], ['Ice Cream', 6, 'Food'], ['Soda', 4, 'Drink']]
# df = pd.DataFrame(data, columns = ['Item', 'Price', 'Type'])
# df

# from itertools import chain, combinations

# def powerset(iterable):
#     "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
#     s = list(iterable)
#     return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

# df_groups = pd.concat([df.reindex(l).assign(grp=n) for n, l in   enumerate(powerset(df.index)) if (df.loc[l, 'Price'].sum() <= 35)])


# df_groups = pd.concat([df.reindex(l).assign(grp=n) for n, l in 
#                        enumerate(powerset(df.index)) 
#                        if ((df.loc[l, 'Price'].sum() <= 35) & 
#                            (df.loc[l, 'Type'].value_counts()==1).all())])
