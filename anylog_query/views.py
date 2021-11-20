from django.shortcuts import render

# Create your views here.
# Import necessary modules
from django.shortcuts import render
from anylog_query.forms import AnyLogCredentials
from django.http import HttpResponse


import anylog_query.json_api as json_api
import anylog_query.anylog_conn.anylog_conn as anylog_conn

ANYLOG_COMMANDS = [
    {'button': 'Node Status',       'command': 'get status', 'type': 'GET'},                        # Get Node Status
    {'button': 'Event Log',         'command': 'get event log where format=json', 'type': 'GET'},   # Get Event Log
    {'button': 'Error Log',         'command': 'get error log where format=json', 'type': 'GET'},   # Get Error Log
    {'button': 'Reset Error',       'command': 'set rest log off', 'type': 'POST'},              # Set REST Log Off
    {'button': 'Set REST',          'command': 'set rest log on', 'type': 'POST'},                  # Set REST Log On
    {'button': 'Get REST',          'command': 'get rest all', 'type': 'GET'},                      # Get REST
    {'button': 'GET REST log',      'command': 'get rest', 'type': 'GET'},                          # GET REST log
    {'button': 'Get Streaming',     'command': 'get streaming', 'type': 'GET'},                     # Get Streaming
    {'button': 'Get Operator',      'command': 'get operator', 'type': 'GET'},                      # Get Operator
    {'button': 'Get Publisher',     'command': 'get publisher', 'type': 'GET'},                     # Get Publisher
    {'button': 'Get Query Status',  'command': 'query status all', 'type': 'GET'},                 # Get Query Status
    {'button': 'Get Last Query Status',     'command': 'query status', 'type': 'GET'},                     # Get Last Query Status
    {'button': 'Get Rows Count',            'command': 'get rows count', 'type': 'GET'},                   # Get Rows Count
    {'button': 'Get Rows Count by Table',   'command': 'get rows count where group=table', 'type': 'GET'}, # Get Rows Count by Table
    {'button': 'Blockchain Operators',      'command': 'blockchain get operator', 'type': 'GET'},          # Blockchain Operators
    {'button': 'Blockchain Publishers',     'command': 'blockchain get publisher', 'type': 'GET'},         # Blockchain Publishers
    {'button': 'Blockchain Queries',        'command': 'blockchain get query', 'type': 'GET'},             # Blockchain Queries
    {'button': 'Blockchain Tables',         'command': 'blockchain get table', 'type': 'GET'},             # Blockchain Tables
]

COMMAND_BY_BUTTON = {}
for index, entry in enumerate(ANYLOG_COMMANDS):
    COMMAND_BY_BUTTON[entry['button']] = index     # Organize commands as f(button)


# ---------------------------------------------------------------------------------------
# GET / POST  AnyLog command form
# ---------------------------------------------------------------------------------------
def form_request(request):

    button = request.POST.get("command")
    if button:
        is_send = button == "send"
    else:
        is_send = False

    # Check the form is submitted or not
    if request.method == 'POST' and is_send:
        user_info = AnyLogCredentials(request.POST)
        # Check the form data are valid or not
        if user_info.is_valid():
            # Proces the command
            command, output = process_anylog(request)

            return print_network_reply(request, user_info, command, output)

            # print to existing screen content of data (currently DNW)
            # return render(request, "base.html", {'form': user_info, 'node_reply': node_reply})

            # print to (new) screen content of data
            # return HttpResponse(data)
    else:
        # Display the html form
        if button:
            request.POST.command = "aaa"
            user_info = AnyLogCredentials(request.POST)     # command selected on the form


            cmd_info = ANYLOG_COMMANDS[COMMAND_BY_BUTTON[button]]
            user_cmd = cmd_info["command"]


            #user_info.fields['command'].intial=user_cmd
            #user_info.data['command'] = user_cmd             # Command to display
        else:
            user_info = AnyLogCredentials()                 # Empty form
        select_info = {}
        select_info["form"] = user_info
        select_info["commands_list"] = ANYLOG_COMMANDS

        return render(request, "base.html", select_info)
# ---------------------------------------------------------------------------------------
# Process the AnyLog command form
# ---------------------------------------------------------------------------------------
def process_anylog(request):
    '''
    :param request: The info needed to execute command to the AnyLog network
    :return: The data to display on the output form
    '''
    authentication = ()
    remote = False

    # Get the needed info from the form
    conn_info = request.POST.get('conn_info')
    username = request.POST.get('username')
    password = request.POST.get('password')
    command = request.POST.get('command')
    anylog_cmd = request.POST.get('anylog_cmd')
    network = request.POST.get('network')

    if network == 'on':
        network = True
    else:
        network = False
    post = request.POST.get('post')
    if post == 'on':
        post = True
    else:
        post = False

    if anylog_cmd is not None:
        anylog_cmd = int(anylog_cmd)
        if ANYLOG_COMMANDS[anylog_cmd]['type'] == 'POST':
            post = True

        command = ANYLOG_COMMANDS[anylog_cmd]['command']

    authentication = ()
    if username != '' and password != '':
        authentication = (username, password)

    if post is True:
        output = anylog_conn.post_cmd(conn=conn_info, command=command, authentication=authentication)
    else:
        output = anylog_conn.get_cmd(conn=conn_info, command=command, authentication=authentication, remote=network)

    return [command, output]     # Data returned from AnyLog or an Error Message



# -----------------------------------------------------------------------------------
# Print network reply -
# Option 1 - a tree
# Option 2 - a table
# Option 3 - text
# -----------------------------------------------------------------------------------
def print_network_reply(request, user_info, command, data):

    select_info = {}
    select_info['form'] = user_info
    select_info['title'] = 'Network Command'
    select_info['command'] = command
    select_info["commands_list"] = ANYLOG_COMMANDS


    policy, table_info, print_info, error_msg = format_message_reply(data)
    if policy:
        # Reply was a JSON policy
        data_list = []
        json_api.setup_print_tree(policy, data_list)
        select_info['text'] = data_list
        return render(request, 'output_tree.html', select_info)

    if table_info:
        # Reply is structured as a table

        if 'header' in table_info:
            select_info['header'] = table_info['header']
        if 'table_title' in table_info:
            select_info['table_title'] = table_info['table_title']
        if 'rows' in table_info:
            select_info['rows'] = table_info['rows']
        return render(request, 'output_table.html', select_info)


    select_info['text'] = print_info        # Only TEXT

    return render(request, 'output_cmd.html', select_info)

# -----------------------------------------------------------------------------------
# Based on the message reply - organize as a table or as an attrubute values list
# -----------------------------------------------------------------------------------
def format_message_reply(msg_text):
    '''
    Return 4 values depending on the type of message:
    policy
    table_info (header, title and rows)
    Text List (entries are attr - val pairs)
    '''

    # If the message is a dictionary or a list - return the dictionary or the list

    policy = None
    error_msg = None
    if msg_text[0] == '{' and msg_text[-1] == '}':
        policy, error_msg = json_api.string_to_json(msg_text)

    elif msg_text[0] == '[' and msg_text[-1] == ']':
        policy, error_msg = json_api.string_to_list(msg_text)

    if policy or error_msg:
        return [policy, None, None, error_msg]  # return the dictionary or the list


    # Make a list of strings to print
    data = msg_text.replace('\r', '')
    text_list = data.split('\n')


    # Test id the returned message is formatted as a table
    table_data = {}
    is_table = False
    for index, entry in enumerate(text_list):
        if entry and index:
            if entry[0] == '-' and entry[-1] == '|':
                # Identified a table
                is_table = True
                columns_list = entry.split('|')
                columns_size = []
                for column in columns_list:
                    if len(column):
                        columns_size.append(len(column))     # An array with the size of each column
                header = []
                offset = 0
                for column_id, size in enumerate(columns_size):
                    header.append(text_list[index - 1][offset:offset + size])
                    offset += (size + 1)                # Add the field size and the separator (|)

                table_data['header'] = header
                if index > 1 and len(text_list[index -2]):
                    table_data['table_title'] = text_list[index -2]         # Get the title if available
                break
        if index >= 5:
            break  # not a table

    if is_table:
        # a Table setup and print
        table_rows = []
        for y in range(index + 1, len(text_list)): # Skip the dashed separator to the column titles
            row = text_list[y]

            columns = []
            offset = 0
            for column_id, size in enumerate(columns_size):
                columns.append(row[offset:offset + size])
                offset += (size + 1)  # Add the field size and the separator (|)

            table_rows.append(columns)

        table_data['rows'] = table_rows
        return [None, table_data, None, None]

    # Print Text

    data_list = []     # Every entry holds type of text ("text" or "Url) and the text string

    for entry in text_list:
        # Setup URL Link (reply to help command + a link to the help page)
        if entry[:6] == "Link: ":
            index = entry.rfind('#')  # try to find name of help section
            if index != -1:
                section = entry[index + 1:].replace('-', ' ')
            else:
                section = ""
            data_list.append(("url", entry[6:], section))
        else:
            # Split text to attribiute value using colon
            if entry:
                key_val = entry.split(':', 1)
                key_val.insert(0, "text")

                data_list.append(key_val)

    return [None, None, data_list, None]
