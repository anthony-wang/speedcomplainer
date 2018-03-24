println("Parsing speedresults.csv")

datef = Dates.DateFormat("yyyy-mm-dd HH:MM:SS");
test_time_format = Dates.format(now(),datef);

fhandle = open("../data/speedresults.csv","r")
@time raw = CSV.read(fhandle;
    delim = ";",
    dateformat = datef,
    header = ["Date", "DL", "UL", "Ping"],
    datarow = 2,
    types = [DateTime, Float64, Float64, Float64],
    nullable = false, # nullable must be false, since there are no plot recipes for Nullables
    weakrefstrings = false)
close(fhandle)

println("Parsing speedresults done")
