# Put the directory of 'DNest4/code' into this variable
DNEST4_PATH = DNest4/code

EIGEN_PATH = eigen

CELERITE_PATH = celerite/cpp/include


includes = -I$(DNEST4_PATH) -I$(EIGEN_PATH) -I$(CELERITE_PATH)

CXX = g++
CXXFLAGS = -pthread -std=c++11 -O3 -DNDEBUG -w
LIBS = -ldnest4 -L/usr/local/lib


SRCDIR = ./src
SRCS =\
$(SRCDIR)/Data.cpp \
$(SRCDIR)/main.cpp \
$(SRCDIR)/MyConditionalPrior.cpp \
$(SRCDIR)/MyModel.cpp

OBJS=$(subst .cpp,.o,$(SRCS))
HEADERS=$(subst .cpp,.h,$(SRCS))

all: main

%.o: %.cpp
	$(CXX) -c $(includes) -o $@ $< $(CXXFLAGS)


main: $(OBJS)
	$(CXX) -o main $(OBJS) -L$(DNEST4_PATH) $(LIBS) $(CXXFLAGS)

clean:
	rm -f main $(OBJS)

cleanout:
	rm -f sample.txt sample_info.txt levels.txt weights.txt posterior_sample.txt sampler_state.txt

cleanall: clean
	rm -f sample.txt sample_info.txt levels.txt weights.txt posterior_sample.txt sampler_state.txt
