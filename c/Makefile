FILES = $(shell python3 files.py)

CC=emcc
CFLAGS=-o build/emcc/add2.wasm --no-entry \
       -O3 \
       -s ALLOW_MEMORY_GROWTH=1 \
       -s INITIAL_MEMORY=16MB \
       -IInclude \
#       -s EXPORTED_FUNCTIONS='["_main"]'\
#       -s LINKABLE=1 -s EXPORT_ALL=1 -s SIDE_MODULE=1\
#        \
#       -gsource-map --source-map-base 'http://localhost:8080/c/build/emcc/' \

ccore: add.c Objects/object.c Objects/short.c Objects/longobject.c Objects/tupleobject.c
	$(CC) Objects/*.c add.c  $(CFLAGS) -s EXPORTED_FUNCTIONS=$(FILES)

