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

# note the "@df" macro requires StatPlots.jl

StatPlots.plot(raw[:Date], hcat(raw[:DL], raw[:UL], raw[:Ping]),
    axis=[:l :l :r],
    seriestype = :line,
    legend = :bottomright,
    title = "#VodafoneDE internet speed history",
    label = ["DL" "UL" "Ping"],
    linewidth = 1,
    # smooth = true,
    # line = :red,
    xlabel = "Time",
    ylabel = "Speed")
# Plots.plot!(raw[:Date], raw[:Ping], axis=[:r])
