
import streamlit as st
import pandas as pd
import numpy as np
from st_aggrid import AgGrid
import math
from pyomo.environ import *
from pyomo.opt import SolverFactory


#st.set_page_config(layout="wide")

url = """https://docs.google.com/spreadsheets/d/1gd_SJn1AMJFXrfwIWglTfkImdNySX32zWGB0DYW4q4A/gviz/tq?tqx=out:csv&sheet=student_details"""
df = pd.read_csv(url).drop_duplicates(keep = 'first')

st.header('World Wide Learning')

st.subheader('Student Details')
AgGrid(df)

@st.cache
def convert_df(df):
    return df.to_csv().encode('utf-8')


#############################################################################################

def get_weekday_availability(utc_plus_time):
    availability = []
    end = -utc_plus_time + 21 
    availability = list(range(math.ceil(-utc_plus_time + 16), math.floor(end+ 1 ) )   )
    if -utc_plus_time + 21 > 23:
        end = -utc_plus_time + 21 - 23
        availability = list(range(math.ceil(-utc_plus_time + 16),23)   ) + list(range(math.floor(end)  )   )
    return availability

def get_weekend_availability(utc_plus_time):
    availability = []
    end = -utc_plus_time + 21 
    availability = list(range(math.ceil(-utc_plus_time + 9), math.floor(end+ 1 ) )   )
    if -utc_plus_time + 21 > 23:
        end = -utc_plus_time + 21 - 23
        availability = list(range(math.ceil(-utc_plus_time + 16),23)   ) + list(range(math.floor(end)  )   )
    return availability


####################################################################################################################


#stdt_lst =  [11009, 11142, 11019, 11021, 11022, 11156, 11029, 11033, 11176, 11049, 11178, 11052, 11186, 11059, 11187, 11062, 11065, 11194, 11196, 11204, 11083, 11091, 11095, 11104, 11111, 11121, 11123, 11001, 11003]


df1 = df.groupby(['module','english_lvl'], as_index=False)['student_id'].agg(lambda x: list(set(x)))






def get_weekday_schedule(module , english_lvl, stdt_lst):
    temp = df[df.student_id.isin(stdt_lst)][['student_id','utc_plus_time']].drop_duplicates(keep = 'first')
    temp['weekday_slots'] = temp['utc_plus_time'].apply(get_weekday_availability)
    student_slot_dict = pd.Series(temp.weekday_slots.values,index=[ 'student_' + str(i) for i in temp.student_id]).to_dict()
    temp = temp.drop(['utc_plus_time'], axis = 1).reset_index(drop = True)

    model = ConcreteModel()
    slot_utc = {}
    
    max_grp_per_time = math.floor(len(stdt_lst)/6)
    for i in range(24*max_grp_per_time):
        slot_utc['slot_'+str(i)] = 'utc_'+str(math.floor(i/max_grp_per_time))
    
    students = ['student_' + str(i) for i in list(temp.student_id)]  # 10 workers available, more than needed
    model.slot_required = Var(  list(slot_utc.keys()), domain=Binary, initialize=0)
    model.works = Var(((student, slot) for student in students for slot in list(slot_utc.keys())  ),
                      within=Binary, initialize=0)

    model.obj = Objective(expr = sum(model.slot_required[i] for i in list(slot_utc.keys())), sense=minimize)
    model.constraints = ConstraintList()  
    
    for slot in list(slot_utc.keys()):
        model.constraints.add(sum(model.works[student, slot] for student in students ) <=6)
    
    for slot in list(slot_utc.keys()):
        for student in students:
            model.constraints.add( model.works[student, slot] <= model.slot_required[slot]  )
    
    for student in students:
        model.constraints.add(sum(model.works[student, slot] for slot in list(slot_utc.keys())  ) == 1)
        ava_slot = student_slot_dict[student]
        ava_slot = ['utc_'+str(i) for i in ava_slot]
        slot_lst = [i for i in list(slot_utc.keys()) if slot_utc[i] not in ava_slot]
        for slot in slot_lst:
            model.constraints.add(model.works[student, slot] == 0)
            
    results =  SolverFactory('cbc').solve(model)
    students_slot = [model.works[student, slot].value for student in students for slot in list(slot_utc.keys()) ]
    
    weekday_student_slot_allocation = {}
    for slot in list(slot_utc.keys()):
        weekday_student_slot_allocation[slot] = []
    
    
    for student in students:
        weekday_student_slot_allocation[slot] = []
        for slot in list(slot_utc.keys()):
            if model.works[student, slot].value == 1:
                weekday_student_slot_allocation[slot].append(student)
    
    for i in list(weekday_student_slot_allocation.keys()):
        if len(weekday_student_slot_allocation[i]) == 0:
            del weekday_student_slot_allocation[i]
            
    
    weekday_schedule_temp = pd.DataFrame(weekday_student_slot_allocation.items(),  columns=['slot', 'student_id'] )        
    weekday_schedule_temp['time_in_utc'] = weekday_schedule_temp.slot.apply(lambda x: slot_utc[x])
    weekday_schedule_temp = weekday_schedule_temp.drop(['slot'], axis = 1).reset_index(drop = True)
    weekday_schedule_temp['english_lvl'] = english_lvl
    weekday_schedule_temp['module'] = module
    return weekday_schedule_temp


weekday_schedule = pd.DataFrame(columns = ['student_id', 'time_in_utc', 'english_lvl','module' ])

if st.button('Get the weekday schedule'):

    for i in range(df1.shape[0]):
        weekday_schedule = pd.concat([weekday_schedule, get_weekday_schedule(df1.iloc[i,0], df1.iloc[i,1], df1.iloc[i,2])  ])
    st.header('')

    st.subheader('Weekday Schedule')
    AgGrid(weekday_schedule)
    
    csv = convert_df(weekday_schedule)
    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name='weekday_schedule.csv',
        mime='text/csv')



########################################################################################################################



def get_weekend_schedule(module , english_lvl, stdt_lst):
    temp = df[df.student_id.isin(stdt_lst)][['student_id','utc_plus_time']].drop_duplicates(keep = 'first')
    temp['weekend_slots'] = temp['utc_plus_time'].apply(get_weekend_availability)
    student_slot_dict = pd.Series(temp.weekend_slots.values,index=[ 'student_' + str(i) for i in temp.student_id]).to_dict()
    temp = temp.drop(['utc_plus_time'], axis = 1).reset_index(drop = True)

    model = ConcreteModel()
    slot_utc = {}
    
    max_grp_per_time = math.floor(len(stdt_lst)/6)
    for i in range(24*max_grp_per_time):
        slot_utc['slot_'+str(i)] = 'utc_'+str(math.floor(i/max_grp_per_time))
    
    students = ['student_' + str(i) for i in list(temp.student_id)]  # 10 workers available, more than needed
    model.slot_required = Var(  list(slot_utc.keys()), domain=Binary, initialize=0)
    model.works = Var(((student, slot) for student in students for slot in list(slot_utc.keys())  ),
                      within=Binary, initialize=0)

    model.obj = Objective(expr = sum(model.slot_required[i] for i in list(slot_utc.keys())), sense=minimize)
    model.constraints = ConstraintList()  
    
    for slot in list(slot_utc.keys()):
        model.constraints.add(sum(model.works[student, slot] for student in students ) <=6)
    
    for slot in list(slot_utc.keys()):
        for student in students:
            model.constraints.add( model.works[student, slot] <= model.slot_required[slot]  )
    
    for student in students:
        model.constraints.add(sum(model.works[student, slot] for slot in list(slot_utc.keys())  ) == 1)
        ava_slot = student_slot_dict[student]
        ava_slot = ['utc_'+str(i) for i in ava_slot]
        slot_lst = [i for i in list(slot_utc.keys()) if slot_utc[i] not in ava_slot]
        for slot in slot_lst:
            model.constraints.add(model.works[student, slot] == 0)
            
    results =  SolverFactory('cbc').solve(model)
    students_slot = [model.works[student, slot].value for student in students for slot in list(slot_utc.keys()) ]
    
    weekend_student_slot_allocation = {}
    for slot in list(slot_utc.keys()):
        weekend_student_slot_allocation[slot] = []
    
    
    for student in students:
        weekend_student_slot_allocation[slot] = []
        for slot in list(slot_utc.keys()):
            if model.works[student, slot].value == 1:
                weekend_student_slot_allocation[slot].append(student)
    
    for i in list(weekend_student_slot_allocation.keys()):
        if len(weekend_student_slot_allocation[i]) == 0:
            del weekend_student_slot_allocation[i]
            
    
    weekend_schedule_temp = pd.DataFrame(weekend_student_slot_allocation.items(),  columns=['slot', 'student_id'] )        
    weekend_schedule_temp['time_in_utc'] = weekend_schedule_temp.slot.apply(lambda x: slot_utc[x])
    weekend_schedule_temp = weekend_schedule_temp.drop(['slot'], axis = 1).reset_index(drop = True)
    weekend_schedule_temp['english_lvl'] = english_lvl
    weekend_schedule_temp['module'] = module
    return weekend_schedule_temp


weekend_schedule = pd.DataFrame(columns = ['student_id', 'time_in_utc', 'english_lvl','module' ])

if st.button('Get the weekend schedule'):
    for i in range(df1.shape[0]):
        weekend_schedule = pd.concat([weekend_schedule, get_weekend_schedule(df1.iloc[i,0], df1.iloc[i,1], df1.iloc[i,2])  ])

    st.header('')
    st.subheader('Weekend Schedule')
    AgGrid(weekend_schedule)
    
    csv = convert_df(weekend_schedule)
    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name='weekend_schedule.csv',
        mime='text/csv')

