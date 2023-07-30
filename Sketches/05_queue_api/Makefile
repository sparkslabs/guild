all:
	g++ --std=c++2a staged.cpp -o staged
	g++ --std=c++2a built-up.cpp -o built-up 
	./mkActor.py built-up.cpp

mkactor:
	mkActor.py built-up.cpp

run:
	./staged
	./built-up 


distclean:
	rm -f staged
	rm -f *~

clean:
	rm -f staged
	rm -f built-up
	rm -f *~

