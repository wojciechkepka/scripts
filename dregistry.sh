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

	IMAGE='image_name'
		PROJECT='project-name'
		BLD_DIR='/path/to/image/src'
	IMAGE='second_image'
		...
	\"\"\"
"
	print_help
}

print_help() {
	echo "Usage:
	dregistry do <IMAGE> [TAG]	- Builds, tags and pushes specified image to registry
	dregistry login <TOKEN>		- Saves login token in config file
	dregistry list			- Lists images defined in config file
	dregistry help			- Print full help message
"
}

: << 'DOC'
Checks if the command was successful. If not prints error message and quits with exit code 1
Parameters:
	$1 - Exit code of command
	$2 - Error message
DOC
if_failed() {
	local exit_code=$1
	local err_msg=$2
	if [ $exit_code -ne 0 ]
	then
		echo "$err_msg"
		exit 1
	fi
}

: << 'DOC'
Checks if the passed variable is not null. If it is prints error message or sets a default value.
Parameters:
	$1 - variable
	$2 - Error message starting with 'Error: ' or default value
Exports:
	$READ_ARG_RET - value of the arg
DOC
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

: << 'DOC'
Checks if specified variable name is set globally. If not prints error message
Parameters:
	$1 - Variable name
	$2 - Error message
DOC
check_arg() {
	local arg_name="$1"
	local err_msg="$2"
	if [[ -z ${!arg_name} ]]
	then
		echo "$err_msg"
		exit 1
	fi
}


: << 'DOC'
Exports:
	$DREGISTRY_CONF - Location of configuration file
DOC
get_cfg_location() {
	if [[ -z $DREGISTRY_CONF ]]
	then
		if [ -f $HOME/.dregistry.conf ]
		then
			DREGISTRY_CONF="$HOME/.dregistry.conf"
		else
			about
			echo "Error: configuration file not found in $HOME/.dregistry.conf and DREGISTRY_CONF env var not set"
			exit 1
		fi
	fi
}

: << 'DOC'
Exports:
	$DREGISTRY_CONF_LINES - Array of lines from file separated by '\n'
DOC
load_conf_file() {
	DREGISTRY_CONF_LINES=()
	while IFS= read -r line
	do
		DREGISTRY_CONF_LINES+=("$line")
	done < "$DREGISTRY_CONF"
}

: << 'DOC'
Exports:
	$DREGISTRY_IMAGES - Array of image names from config file 
DOC
read_images_from_cfg() {
	load_conf_file

	for line in "${DREGISTRY_CONF_LINES[@]}"
	do
		if [[ $line =~ ^IMAGE=[\'\"](.*)[\'\"]$ ]];
		then
			DREGISTRY_IMAGES+=( "${BASH_REMATCH[1]}" )
		fi
	done
}

: << 'DOC'
Parses configuration for specified image from $DREGISTRY_CONF_LINES
Parameters:
	$1 - Name of the image
Exports:
	$DOCKER_REGISTRY, $LOGIN_TOKEN	- Global settings (last line read applies)
	$PROJECT, $BLD_DIR			- Image specific settings
DOC
read_cfg_for_image() {
	local image_name="$1"
	local found_image=false

	load_conf_file

	for line in "${DREGISTRY_CONF_LINES[@]}"
	do
		if [[ $line =~ ^DOCKER_REGISTRY=[\'\"](.*)[\'\"]$ ]]
		then
			DOCKER_REGISTRY="${BASH_REMATCH[1]}"
		elif [[ $line =~ ^LOGIN_TOKEN=[\'\"](.*)[\'\"]$ ]]
		then
			LOGIN_TOKEN="${BASH_REMATCH[1]}"
		else
			if [[ $line =~ ^IMAGE=[\'\"]$image_name[\'\"]$ ]]
			then
				found_image=true
			elif [[ $line =~ ^[[:blank:]]+PROJECT=[\'\"](.*)[\'\"]$ ]] \
			&& [ $found_image ]
			then
				PROJECT="${BASH_REMATCH[1]}"
			elif [[ $line =~ ^[[:blank:]]+BLD_DIR=[\'\"](.*)[\'\"]$ ]] \
			&& [ $found_image ]
			then
				BLD_DIR="${BASH_REMATCH[1]}"
			fi
		fi
	done

	check_arg "PROJECT" "Error: PROJECT variable missing from config for image $image_name"
	check_arg "BLD_DIR" "Error: BLD_DIR variable missing from config for image $image_name"
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

: << 'DOC'
Asks user to confirm the build.
Exports:
	$DREGISTRY_BUILD - Users answer
DOC
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
				DREGISTRY_BUILD="false"
				got_answer=true
				break
				;;
		esac
	done
}


cmd_do() {
	read_arg "$1" "Error: provide image name to build and push"
	IMAGE=$READ_ARG_RET
	read_arg "$2" "latest"
	TAG=$READ_ARG_RET

	get_cfg_location
	read_cfg_for_image "$IMAGE"
	print_info
	confirm_build
	if [[ $DREGISTRY_BUILD == true ]]
	then
		docker login -p $LOGIN_TOKEN -u unused $DOCKER_REGISTRY
		if_failed $? "Error: failed to login to $DOCKER_REGISTRY using $LOGIN_TOKEN"

		docker build --tag $DOCKER_REGISTRY/$PROJECT/$IMAGE:$TAG $BLD_DIR
		if_failed $? "Error: failed to build image $IMAGE"
		docker push $DOCKER_REGISTRY/$PROJECT/$IMAGE:$TAG
	fi

	exit 0
}

cmd_login() {
	local auth_token="$1"
	get_cfg_location
	echo "Changing auth token in '$DREGISTRY_CONF' to '$auth_token'"
	sed -i -e "s/^LOGIN_TOKEN=[\'\"].*[\'\"]$/LOGIN_TOKEN='$auth_token'/g" $DREGISTRY_CONF
	exit 0
}

cmd_list() {
	get_cfg_location
	read_images_from_cfg
	echo "Available images:"
	for img in "${DREGISTRY_IMAGES[@]}"
	do
		echo -e "\t$img"
	done
}

###############################################################################

read_arg "$1" "Error: provide a subcommand to run"
SUBCOMMAND=$READ_ARG_RET
shift

case $SUBCOMMAND in
	"do")
		cmd_do "$1" "$2"
		;;
	"login")
		cmd_login "$1"
		;;
	"list")
		cmd_list
		;;
	"help")
		about
		;;
	*)
		print_help
		echo "Error: unknown command $SUBCOMMAND"
		exit 1
esac



