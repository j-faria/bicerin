#include <iostream>
#include "Data.h"
//#include "MultiSite2.h"
#include "Start.h"
#include "MyModel.h"

using namespace std;
using namespace DNest4;

int main(int argc, char** argv)
{

	Data::get_instance().loadnew("data/HD41248.rdb");
    //return 0;

	start<MyModel>(argc, argv);
	return 0;
}
