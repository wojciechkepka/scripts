#!/bin/bash

about() {
	echo "dregistry
Script to make building and pushing docker images quicker.

Configuration:
	By default this script will look for a config file in '~/.dregistry.conf'. You can override
	default location by setting environment variable DREGISTRY_CONF pointing at the config file.

Example config file syntax (skip \"\"\"):
	\"\"\"
	DOCKER_REGISTRY='docker.registry.mydomain.com'
	LOGIN_TOKEN='F0yWnVU2YtSjlBYpFA5_0-IRO9VcnLUvc1x7gWZwA4-'

	image_name
		PROJECT='project-name'
		BLD_DIR='/path/to/image/src'
	second_image
		...
	\"\"\"
"
	print_help
}
print_help() {
	echo "Usage:
	dregistry <IMAGE> [TAG]
"
}

if_failed() {
	local exit_code=$1
	local err_msg=$2
	if [ $exit_code -ne 0 ]
	then
		echo "$err_msg"
		exit 1
	fi
}

read_arg() {
	if [[ -n $1 ]]
	then
		READ_ARG_RET="$1"
	else
		if [[ $2 =~ ^Error:.* ]]
		then
			# In case of printing an error message
			print_help
			echo "$2"
			exit 1
		else
			# Case with default value
			READ_ARG_RET="$2"
		fi
	fi
}

check_arg() {
	local arg_name="$1"
	local err_msg="$2"
	if [[ -z ${!arg_name} ]]
	then
		echo "$err_msg"
		exit 1
	fi
}

get_cfg_location() {
	if [[ -z $DREGISTRY_CONF ]]
	then
		if [ -f "~/.dregistry.conf" ]
		then
			DREGISTRY_CONF="~/.dregistry.conf"
		else
			about
			echo "Error: configuration file not found in ~/.dregistry.conf and DREGISTRY_CONF env var not set"
			exit 1
		fi
	fi

}

read_cfg() {
	local conf_file_path="$1"
	local conf_file=()
	while IFS= read -r line
	do
		conf_file+=("$line")
	done < "$conf_file_path"

	local found_image=false

	for line in "${conf_file[@]}"
	do
		if [[ $line =~ ^DOCKER_REGISTRY=\"(.*)\" ]]
		then
			DOCKER_REGISTRY="${BASH_REMATCH[1]}"
		elif [[ $line =~ ^LOGIN_TOKEN=\"(.*)\" ]]
		then
			LOGIN_TOKEN="${BASH_REMATCH[1]}"
		else
			if [[ $line =~ ^$2 ]]
			then
				found_image=true
			elif [[ $line =~ PROJECT=[\'\"](.*)[\'\"] ]] \
			&& [ $found_image ]
			then
				PROJECT="${BASH_REMATCH[1]}"
			elif [[ $line =~ BLD_DIR=[\'\"](.*)[\'\"] ]] \
			&& [ $found_image ]
			then
				BLD_DIR="${BASH_REMATCH[1]}"
			fi
		fi
	done

	check_arg "PROJECT" "Error: PROJECT variable missing from config for image $2"
	check_arg "BLD_DIR" "Error: BLD_DIR variable missing from config for image $2"
}

print_info() {
	echo -e "Build info:
-----------------
DOCKER_REGISTRY:\t$DOCKER_REGISTRY
AUTH_TOKEN:\t\t$LOGIN_TOKEN
PROJECT:\t\t$PROJECT
IMAGE:\t\t\t$IMAGE
TAG:\t\t\t$TAG
BLD_DIR:\t\t$BLD_DIR
"
}
confirm_build() {
	local got_answer=false
	while [ $got_answer != true ]
	do
		echo "Continue building? y/n"
		read do_build
		case $do_build in
			'y')
				DREGISTRY_BUILD="true"
				got_answer=true
				break
				;;
			'n')
				got_answer=true
				break
				;;
		esac
	done
}
###############################################################################

read_arg "$1" "Error: provide image name to build and push"
IMAGE=$READ_ARG_RET
read_arg "$2" "latest"
TAG=$READ_ARG_RET

get_cfg_location
read_cfg "$DREGISTRY_CONF" "$IMAGE"
print_info
confirm_build

################################################################################


if [ $DREGISTRY_BUILD == true ]
then
	docker login -p $LOGIN_TOKEN -u unused $DOCKER_REGISTRY
	if_failed $? "Error: failed to login to $DOCKER_REGISTRY using $LOGIN_TOKEN"

	docker build --tag $DOCKER_REGISTRY/$PROJECT/$IMAGE:$TAG $BLD_DIR
	if_failed $? "Error: failed to build image $IMAGE"
	docker push $DOCKER_REGISTRY/$PROJECT/$IMAGE:$TAG
fi

