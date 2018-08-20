#!/bin/sh
set -e

usage()
{
	echo "${0} Usage:"
	echo "	-i <inputfile>,	the encrypted mansion package(.pkg) wait to be dencrypted."
	echo "	-o <outputdir>,	the output dir for package verify and dencrpytion output."
	echo "	               	default: inputfile's dir."
	echo "	-k <pubkey>,	the RSA public key for this dencryption."
}

OPTS="i:k:o:"
while getopts ${OPTS} OPT; do
	case ${OPT} in
	i)
		export MANSION_SRC_ROOT=$(dirname ${OPTARG})
		export MANSION_SRC_FILE=$(basename ${OPTARG})
		export MANSION_RLS_FILE=${MANSION_SRC_FILE%%.pkg}
		;;
	o)
		export MANSION_RLS_ROOT=${OPTARG}
		;;
	k)
		export MANSION_KEY_ROOT=$(dirname ${OPTARG})
		export MANSION_KEY_PUB=$(basename ${OPTARG})
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
	 -z "${MANSION_RLS_FILE}" -o \
	 -z "${MANSION_KEY_ROOT}" -o \
	 -z "${MANSION_KEY_PUB}" ]; then
	echo "${0}: Missing argument" >&2
	usage
	exit 1
fi

if [ -z "${MANSION_RLS_ROOT}" ]; then
	export MANSION_RLS_ROOT=${MANSION_SRC_ROOT}
fi

echo "Verify ${MANSION_RLS_PKG} for mansion......"
echo "--------------"
echo "	Preparing the verify environment..."
TMP_BUILD_DIR=$(mktemp -d)

echo "	Dencryped to: ${TMP_BUILD_DIR}/"
tar -xf ${MANSION_SRC_ROOT}/${MANSION_SRC_FILE} -C ${TMP_BUILD_DIR} || true
openssl pkeyutl -verifyrecover -in ${TMP_BUILD_DIR}/${MANSION_RLS_FILE}.sig \
-pubin -inkey ${MANSION_KEY_ROOT}/${MANSION_KEY_PUB} \
-out ${TMP_BUILD_DIR}/${MANSION_RLS_FILE}.key || true
echo "	Key ReGenerated."

openssl enc -aes-256-ecb -in ${TMP_BUILD_DIR}/${MANSION_RLS_FILE}.tgt \
-out ${TMP_BUILD_DIR}/${MANSION_RLS_FILE} \
-kfile ${TMP_BUILD_DIR}/${MANSION_RLS_FILE}.key -d || true
echo "	Verify Ok: ${MANSION_RLS_FILE}"

mv -f ${TMP_BUILD_DIR}/${MANSION_RLS_FILE} ${MANSION_RLS_ROOT}/${MANSION_RLS_FILE} || true

echo "	Clean over the verify enviroment..."
rm -rf ${TMP_BUILD_DIR}

echo "	Done."
