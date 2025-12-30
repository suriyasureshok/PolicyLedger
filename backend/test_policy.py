import json

policy_data = json.load(open('policies/3f6a62d2aea4d97731d1eb57aafb4f9da9d2ddb34a8c476b6b1b138e84ca8443.json'))
print('Sample policy keys:')
for i, key in enumerate(list(policy_data['policy'].keys())[:5]):
    print(f'{i+1}. Key: {repr(key)} (Type: {type(key).__name__}) -> Action: {policy_data["policy"][key]}')

print('\nTest state conversion:')
test_state = (1, 1, 1, 0, 0)
str_state = str(test_state)
print(f'Tuple: {test_state}')
print(f'String: {repr(str_state)}')
print(f'In policy: {str_state in policy_data["policy"]}')
