#!/bin/sh
set -e

usage()
{
	echo "${0} Usage:"
	echo "	-i <inputfile>,	the pathfile wait to be encrypted."
	echo "	-o <outputdir>,	the output dir for release package output."
	echo "	               	default: inputfile's dir."
	echo "	-k <privatekey>,	the RSA private key for this encryption."
}

OPTS="i:k:o:"
while getopts ${OPTS} OPT; do
	case ${OPT} in
	i)
		export MANSION_SRC_ROOT=$(dirname ${OPTARG})
		export MANSION_SRC_FILE=$(basename ${OPTARG})
		;;
	o)
		export MANSION_RLS_ROOT=${OPTARG}
		;;
	k)
		export MANSION_KEY_ROOT=$(dirname ${OPTARG})
		export MANSION_KEY_PRV=$(basename ${OPTARG})
		;;
	*)
		echo "${0}: Unknown argument '${OPT}'" >&2
		usage
		exit 1
		;;
	esac
done

if [ -z "${MANSION_SRC_ROOT}" -o \
	 -z "${MANSION_SRC_FILE}" -o \
	 -z "${MANSION_KEY_ROOT}" -o \
	 -z "${MANSION_KEY_PRV}" ]; then
	echo "${0}: Missing argument" >&2
	usage
	exit 1
fi

if [ -z "${MANSION_RLS_ROOT}" ]; then
	export MANSION_RLS_ROOT=${MANSION_SRC_ROOT}
fi

export MANSION_RLS_TGT=${MANSION_SRC_FILE}.tgt
export MANSION_RLS_SIG=${MANSION_SRC_FILE}.sig
export MANSION_RLS_PKG=${MANSION_SRC_FILE}.pkg
export MANSION_RLS_KEY=${MANSION_SRC_FILE}.key

echo "Build ${MANSION_RLS_PKG} for publish......"

echo "--------------"
echo "	Preparing the building environment..."
TMP_BUILD_DIR=$(mktemp -d)

echo "	Start building at ${TMP_BUILD_DIR} for ${MANSION_RLS_SRC}"
echo "	Generating random..."
cat /dev/urandom|head -c 128|md5sum >  ${TMP_BUILD_DIR}/${MANSION_RLS_KEY} || true

echo "	Encryped file: ${TMP_BUILD_DIR}/${MANSION_RLS_TGT}"
openssl enc -aes-256-ecb -in ${MANSION_SRC_ROOT}/${MANSION_SRC_FILE} \
-out ${TMP_BUILD_DIR}/${MANSION_RLS_TGT} \
-kfile ${TMP_BUILD_DIR}/${MANSION_RLS_KEY} -e || true

echo "	Signature file: ${TMP_BUILD_DIR}/${MANSION_RLS_SIG}"
openssl pkeyutl -sign -in ${TMP_BUILD_DIR}/${MANSION_RLS_KEY} \
-inkey ${MANSION_KEY_ROOT}/${MANSION_KEY_PRV} \
-out ${TMP_BUILD_DIR}/${MANSION_RLS_SIG} || true

echo "	Package release: ${MANSION_RLS_ROOT}${MANSION_RLS_PKG}"
tar -cf ${MANSION_RLS_ROOT}/${MANSION_RLS_PKG} -C ${TMP_BUILD_DIR} \
${MANSION_RLS_SIG} ${MANSION_RLS_TGT} || true
echo "	Build completed."

echo "	Clean over the building enviroment..."
rm -rf ${TMP_BUILD_DIR}

echo "	Done."
