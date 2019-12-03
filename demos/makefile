CC=gcc
PROGS=loop1 loop2 loop3


all: $(PROGS)

%: %.c
	$(CC) -o $@ $<

clean:
	rm $(PROGS)
