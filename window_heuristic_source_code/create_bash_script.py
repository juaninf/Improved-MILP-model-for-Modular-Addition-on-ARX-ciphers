import sys

with open('docker/Dockerfile', 'r') as f:
    dockerfile_lines = f.readlines()

bash_instructions = ['#!/bin/bash']
docker_command = ''
environment_variables = []
for line in dockerfile_lines:
    line = line.strip()

    if line.startswith("FROM claasp-base AS claasp-lib"):
        break

    is_a_comment = line.startswith('#')
    is_split_command = line.endswith('\\')
    if not line or is_a_comment:
        continue
    if is_split_command:
        docker_command += line[:-1]
        continue

    docker_command += line
    bash_instruction = ''
    if docker_command.startswith('RUN'):
        bash_instruction = docker_command.split('RUN')[1].strip()
    elif docker_command.startswith('ENV'):
        command = docker_command.split('ENV')[1].strip()
        environment_variable = command.split('=')[0]
        if environment_variable not in environment_variables:
            environment_variables.append(environment_variable)
        bash_instruction = f'export {command}'
    elif docker_command.startswith('ARG'):
        command = docker_command.split('ARG')[1].strip()
        bash_instruction = f'export {command}'
    elif docker_command.startswith('WORKDIR'):
        directory = docker_command.split('WORKDIR')[1].strip()
        if directory != '/home/sage/claasp':
            bash_instruction = f'cd {directory}'
    elif docker_command.startswith('COPY'):
        command = docker_command.split('COPY')[1].strip()
        bash_instruction = f'cp {command}'
    else:
        docker_command = ''
        continue

    bash_instructions.append(bash_instruction)
    docker_command = ''

for environment_variable in environment_variables:
    bash_instructions.append(f"echo 'export {environment_variable}='${environment_variable} >> ~/.bashrc")

with open('dependencies_script.sh', 'w') as f:
    f.write('\n\n'.join(bash_instructions))
