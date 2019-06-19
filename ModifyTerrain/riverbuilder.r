#' Generates graphs, text files, and coordinates related to a given set of river data.
#' @param filename Name of the file to be processed.
#' @param directory Path in which outputs will be generated. If non-empty, it must contain "\\\\" or "/" between directories/files, and never "\\". An empty or invalid argument will result in files being generated in a temporary location.
#' @param overwrite Flag that determines whether existing files will be overwritten. If the files already exist and this value is FALSE, the program will stop and produce an error.
#' @return None. Output files are generated in the specified (or temporary) directory: \cr \cr
#' BoundaryPoints.csv - Contains keys that map to specific points in CartesianCoordinates.csv that comprise the boundary around a river’s floodplain.\cr \cr
#' CartesianCoordinates.csv - Contains comma-separated XYZ coordinates for the synthetic river valley. A separate program such as ArcGIS can use these points to generate a 3D model.\cr \cr
#' Data.csv - Contains coefficients of variation, averages, standard deviations, channel slope, and other important information.\cr \cr
#' CenterlineCurvature.png - Displays the curvature of the channel's centerline.\cr \cr
#' CenterlineCurvature.csv - Contains coordinate data that was visualized in CenterlineCurvature.png.\cr \cr
#' ValleySection.png - Displays the cross section of the channel and floodplain at their midway point.\cr \cr
#' ValleySection.csv - Contains coordinate data that was visualized in ValleySection.png.\cr \cr
#' GCS.png - Displays the geometric covariance structures of: bankfull width and thalweg elevation; thalweg elevation and the channel meander.\cr \cr
#' GCS.csv - Contains coordinate data that was visualized in GCS.png.\cr \cr
#' LongitudinalProfile.png - Displays the side view of the river which consists of valley top, valley floor, bank top, and thalweg elevation.\cr \cr
#' LongitudinalProfile.csv - Contains coordinate data that was visualized in LongitudinalProfile.png.\cr \cr
#' Planform.png - Displays the birds eye view of the river which consists of the channel meander, channel bank, valley floor, and valley top.\cr \cr
#' Planform.csv - Contains coordinate data that was visualized in Planform.png.\cr \cr
#' @import grDevices graphics stats utils
#' @examples
#' file <- system.file("extdata", "Input.txt", package="RiverBuilder")
#' riverbuilder(file, '', TRUE)
#' @source \url{http://pasternack.ucdavis.edu/research/projects/synthetic-river-valleys/}
#' @export
riverbuilder = function(filename, directory, overwrite){

if(!file.exists(filename))
	stop("File specified was not found.")

if(directory == '' || typeof(directory) != "character" || !dir.exists(directory))
{
	print("Empty or invalid argument for the directory parameter. Writing to a temporary location.")
	directory = tempdir()
}

file_outputs = c(
	"CenterlineCurvature.png",
	"ValleySection.png",
	"GCS.png",
	"LongitudinalProfile.png",
	"Planform.png",
	"BoundaryPoints.csv",
	"Data.csv",
	"CartesianCoordinates.csv",
	"CenterlineCurvature.csv",
	"ValleySection.csv",
	"GCS.csv",
	"LongitudinalProfile.csv",
	"Planform.csv"
	)

graph_names = c(
	"Centerline Curvature",
	"Cross Section",
	"Geometric Covariance Structures",
	"Longitudinal Profile",
	"Planform"
	)

river_properties = c(
	"Meandering Centerline Function",
	"Centerline Curvature Function",
	"Bankfull Width Function",
	"Thalweg Elevation Function",
	"Left Floodplain Function",
	"Right Floodplain Function",
	"Cross-Sectional Shape"
	)

function_types = c(
	"SIN_SQ",
	"SIN",
	"COS",
	"LINE",
	"PERL"
	)

crossSectionalShapes = c(
	"SU",
	"AU",
	"TZ"
	)


for(i in seq(from=1, to=length(file_outputs), by=1))
{
	coordinate_file = paste(directory, "/", file_outputs[i], sep="")
	if(file.exists(coordinate_file))
	{
		# Remove the file from the directory to avoid appending to the previous data
		if(overwrite)
			file.remove(coordinate_file)
		# Stop program if user wishes to not overwrite files
		else
			stop(paste("One or more output files already exist(s) in '", directory, "'. Program exit.", sep=""))
	}
}

# Generate a random positive or negative value with absolute value < 1 (Perlin function)
random = function()
{
	Zr <<- (Ar * Zr + Cr) %% Mr
	return(Zr / Mr - 0.5)
}

# Return a double value that might involve the constant PI
evaluateNumerical = function(input)
{
	# If the value contains PI, store PI or simplify the expression containing it
	if(grepl("PI", input))
	{
		# The input is "PI", so store the value of pi
		if(input == "PI")
			return(pi)
		else # The input is of the form (a*)PI(/b), where a and/or b are given
		{
			# Ensure that the input is a string. If it isn't, coerce it into a string
			if(typeof(input) != "character")
				input = as.character(input)
			# Acquire the length of the input string for parsing and to avoid seg faults
			length = length(strsplit(input, "")[[1]])
			a = b = ""
			j = 1

			# a is not given
			if(substring(input, 1, 2) == "PI")
			{
				a = "1"
				j = j + 3
			}
			# a is given
			else
			{
				while(substring(input, j, j) != "*")
				{
					a = paste(a, substring(input, j, j), sep="")
					j = j + 1
				}
				j = j + 4
			}

			# b is not given
			if(j > length)
				b = "1"
			# b is given
			else
				b = paste(b, substring(input, j, length), sep="")

			return(as.double(a) * pi / as.double(b))
		}
	}
	# The value is a numerical constant, so just store it
	else
		return(as.double(input))
}

# Store the function that was assigned to a sub-reach variability parameter
storeFunction = function(variable, input)
{
	if(grepl(river_properties[1], variable))
		Mc_functions <<- rbind(Mc_functions, input)
	else if(grepl(river_properties[2], variable))
	{
		# Invalidate the first function since it's not actually used in the computation (asymmetric U)
		if(XS_shape == crossSectionalShapes[2] && nrow(Cs_functions) == 1)
		{
			if(input[1] != function_types[2])
				stop("Please provide a sine function for the AU cross-sectional shape. Program exit.")
			else
				input[1] = "NA"
		}
		Cs_functions <<- rbind(Cs_functions, input)
	}
	else if(grepl(river_properties[3], variable))
		Wbf_functions <<- rbind(Wbf_functions, input)
	else if(grepl(river_properties[4], variable))
		Zt_functions <<- rbind(Zt_functions, input)
	else if(grepl(river_properties[5], variable))
		LeftFP_functions <<- rbind(LeftFP_functions, input)
	else if(grepl(river_properties[6], variable))
		RightFP_functions <<- rbind(RightFP_functions, input)
}

# Evaluate all the functions stored in a variability parameter given independent variables and the associated key
evaluateFunctions = function(functions, ivs, key)
{
	output = 0
	for(i in seq(from=2, to=nrow(functions), by=1))
		output = output + computeFunction(functions[i,], ivs, key)
	return(output)
}

# Evaluate a particular, individual function given independent variables and the associated key
computeFunction = function(fun, iv, key)
{
	output = 0

	if(grepl(function_types[1], fun[1]))
		output = evaluateNumerical(fun[2])*(sin(evaluateNumerical(fun[3])*iv[1] + evaluateNumerical(fun[4])))**2
	else if(grepl(function_types[2], fun[1]))
		output = evaluateNumerical(fun[2])*sin(evaluateNumerical(fun[3])*iv[1] + evaluateNumerical(fun[4]))
	else if(grepl(function_types[3], fun[1]))
		output = evaluateNumerical(fun[2])*cos(evaluateNumerical(fun[3])*iv[1] + evaluateNumerical(fun[4]))
	else if(grepl(function_types[4], fun[1]))
		output = evaluateNumerical(fun[2])*iv[2] + evaluateNumerical(fun[3])
	else if(grepl(function_types[5], fun[1]))
	{
		# For producing the first Perlin point, use the initialized random values
		ra = ga
		rb = gb

		# If previous random values were saved, use them again
		if(!is.null(perlins[[key]]))
		{
			ra = perlins[[key]][1]
			rb = perlins[[key]][2]
		}

		# Create a new sub-wave to ensure randomness in the curve
		if(iv[3] %% evaluateNumerical(fun[3]) < 1)
		{
			ra = rb
			rb = random()
			output = 2*ra*evaluateNumerical(fun[2])
		}
		# Continue with the current sub-wave
		else
		{
			output = interpolate(ra, rb,
				(iv[3] %% evaluateNumerical(fun[3]))/evaluateNumerical(fun[3]))*evaluateNumerical(fun[2])*2
		}

		# Store the random values according to the river property to avoid inter-mixing
		perlins[[key]] <<- rbind(c(ra, rb))
	}

	return(output)
}

# Return whether a given input is a function
isFunction = function(input)
{
	for(i in seq(from=1, to=length(function_types), by=1))
		if(grepl(function_types[i], input))
			return(TRUE)
	return(FALSE)
}

# Return whether a user variable and its defined function are the same
isMatched = function(f1, f2)
{
	for(i in seq(from=1, to=length(function_types), by=1))
		if(grepl(function_types[i], f1) && grepl(function_types[i], f2))
			return(TRUE)
	return(FALSE)

}

# Return whether a function was defined and stored
isDefined = function(input)
{
	return(!is.null(userDefinedFunctions[[input]]))
}

# Formula for standardization (used for information in Data.csv)
standardize = function(x, m, sd)
{
	# Prevent zero-division
	if(sd == 0)
		return(0)
	else
		return( (x-m)/sd )
}

# Ensure that random points connect smoothly in a Perlin wave
interpolate = function(pa, pb, px)
{
	ft = px * pi
	f = (1 - cos(ft)) * 0.5
	return(pa * (1 - f) + pb * f)
}

crossSection = function(type, i, j)
{
	output = 0

	# Symmetric U cross section
	if(type == crossSectionalShapes[1])
		output = topsofBank[i] - bankfullDepths[i]*sqrt((1-(n_xs[i,j]/n_xs[i,1])**2))
	# Asymmetric U cross section (original)
	else if(type == crossSectionalShapes[2])
	{
		if(bankfullWidths[i] != 0)
		{
			if(centerlineCurvatures[i] > 0)
				output = topsofBank[i]-((4*bankfullDepths[i]*(((bankfullWidths[i]/2)-n_xs[i,j])/bankfullWidths[i])^k_s[i])
				* (1-(((bankfullWidths[i]/2)-n_xs[i,j])/bankfullWidths[i])^k_s[i]))
			else
				output = topsofBank[i]-((4*bankfullDepths[i]*((1-((bankfullWidths[i]/2-n_xs[i,j])/bankfullWidths[i]))^k_s[i]))
				* (1-((1-(bankfullWidths[i]/2-n_xs[i,j])/bankfullWidths[i])^k_s[i])))
		}
	}
	# Trapezoidal cross section. Can produce multiple shapes
	else if(type == crossSectionalShapes[3])
	{
		# Triangle: n = 0
		# Trapezoid: 1 <= n <= (ChannelXSPoints-2)
		# Rectangle: (ChannelXSPoints-3) <= n <= ChannelXSPoints

		if(base < 0 || base > ChannelXSPoints)
			stop("Invalid trapezoidal base length. Program exit.")

		inc = 0

		# Assign values based on if the base is even or odd
		if(base %% 2 == 0)
		{
			partition = base/2
			inc = 1
		}
		else
			partition = ceiling(base/2)

		# Endpoints are the bank tops
		if(j == 1 || j == ChannelXSPoints)
			output = topsofBank[i]
		# Produce a negatively-sloped line towards the left vertex of the base
		# or a positively-sloped line towards the right bank top
		else if((j >= 2 && j <= floor(ChannelXSPoints/2)-partition) || j > floor(ChannelXSPoints/2)+partition+inc)
		{
			deltaX = n_xs[i,j]-n_xs[i,j-1]
			deltaY = -bankfullDepths[i]/((ChannelXSPoints/2) - (base/2))
			# Positively-sloped line; switch signs
			if(j > floor(ChannelXSPoints/2)+partition+inc)
				deltaY = -deltaY
			xs_slope = deltaY/deltaX
			output = topsofBank[i] - (ChannelXSPoints/(ChannelXSPoints-base))*bankfullDepths[i] + xs_slope*(n_xs[i,j])
		}
		# Produce the base itself
		else if(j >= floor(ChannelXSPoints/2)-partition+1 && j <= floor(ChannelXSPoints/2)+partition+inc)
			output = topsofBank[i] - bankfullDepths[i]
	}
	# Invalid cross-sectional input
	else
		stop("Invalid input for cross-sectional shape. Program exit.")

	return(output)
}

#############################
#### Initialized Buffers ####
#############################

# Vector that stores every singular parameter value
parameters = c()

# Vector that stores key-value pairs of user defined functions
userDefinedFunctions = c()

# A -> user defined
# B -> calculated from Shields stress and particle size
userDefinedDepth = TRUE

# Sub-variability Function Storage
Mc_functions = data.frame(matrix(ncol=6))
Cs_functions = data.frame(matrix(ncol=6))
Wbf_functions = data.frame(matrix(ncol=6))
Zt_functions = data.frame(matrix(ncol=6))
LeftFP_functions = data.frame(matrix(ncol=6))
RightFP_functions = data.frame(matrix(ncol=6))

# Variable that keeps track of cross-sectional shape defined by the user
XS_shape = ""

# Variable that keeps track of trapezoidal base defined by user (if applicable)
base = 0

# Vector that stores random values associated with each river property (Perlin function)
perlins = c()

# Vector that stores random values associated with each river property (Ferguson, disturbed meander)
fergusons = c()

# Vector that stores powers less than abs(1) for computing points for the cross section
k1 = c()

###############################
#### Input File Processing ####
###############################

print(paste("Generating SRV files in", directory, "..."))

# Read in values from a specified text file.
inputs = read.table(filename, sep="=", header=FALSE, colClasses = c("character"))

# Store every parameter value or user-defined function
for(i in seq(from=1, to=length(inputs$V2), by=1))
{
	# Assign column values for readability
	col1 = (inputs$V1)[i]
	col2 = (inputs$V2)[i]

	input = col2
	input = strsplit(input, split="[(), ]")[[1]]
	input = input[nchar(input)>0]

	# Initialize a user-defined function to be used in future assignments, e.g. SIN#=SIN(a, f, ps)
	if(isFunction(col1))
	{
		if(isMatched(col1, col2) && !isDefined(col1) && grepl("[0-9]", col1))
			userDefinedFunctions[[col1]] = input
		else
			stop("A user-defined function has an invalid name, values, or was defined more than once. Program exit.")
	}
	# Assign a river parameter with a function (user-defined values or function)
	else if(!isFunction(col1) && isFunction(col2))
	{
		# Assign with a function followed by a user-defined set of parameter values, e.g. <PARAMETER> = SIN(a, f, ps)
		if(grepl("(,)", col2))
			storeFunction(col1, input)
		# Assign with a user-defined function, e.g. <PARAMETER>=SIN#
		else
		{
			if(isDefined(col2))
			{
				input = userDefinedFunctions[[col2]]
				storeFunction(col1, input)
			}
			else
				stop("Attempted to assign with an undefined function. Program exit.")
		}
	}
	# EX: <PARAMETER>=(0, 0, 0)
	else if(grepl("(,)", col2))
		stop("Attempted to assign with values but no specific function. Program exit.")
	# Store the cross sectional shape defined by the user
	else if(grepl(river_properties[7], col1))
	{
		if(grepl(crossSectionalShapes[3], col2))
		{
			if(length(input) != 2 || grepl("[A-z]", input[2]) || grepl("[[:punct:]]", input[2]))
				stop("Invalid input for trapezoidal cross section. Program exit.")
			XS_shape = input[1]
			base = as.double(input[2])
		}
		else
			XS_shape = col2
	}
	# Store numerical value
	else
	{
		# If B, calculate channel depth given t50 and D50
		if(grepl("Hbf", col1))
		{
			input = strsplit(col1, ",")[[1]][2]
			if(grepl("B", input))
				userDefinedDepth = FALSE
		}

		parameters = c(parameters, evaluateNumerical(col2))
	}
}

####################
#### Parameters ####
####################

# Domain Parameters
datum = parameters[1]
length = parameters[2]
XResolution = length/parameters[3]
ChannelXSPoints = parameters[4]

# Dimensionless Parameters
valleySlope = parameters[5]
criticalShieldsStress = parameters[6]

# Channel Parameters
bankfullWidth = parameters[7]
bankfullWidthMin = parameters[8]
bankfullDepth = parameters[9]
medianSedimentSize = parameters[10]

# Floodplain Parameters
FPWidth = parameters[11]
outerFPEdgeHeight = parameters[12]
terraceWidth = parameters[13]
outerTerraceEdgeHeight = parameters[14]
boundaryWidth = parameters[15]

#####################
#### Coordinates ####
#####################

# Channel Model
# Column B
increments = c()
# Column C
xrads = c()
# Column D
xms = c()
# Column E
channelMeanders = c()
# Column H
scms = c(0)
# Column I
dscms = c()
# Column J
scms_r = c()
# Column K
dxcmds = c()
# Column L
dycmds = c()
# Column N
thalwegs = c()
# Column P
thalwegsNoSlope = c()
# Column Q
topsofBank = c()
# Column R
bankfullDepths = c()
# Column S
wbf_pfs = c()
# Column T
bankfullWidths = c()
# Column U
bankfullWidths_L = c()
# Column V
bankfullWidths_R = c()
# Column W
centerlineCurvature_pfs = c()
# Column X
firstDerivatives = rep(0, XResolution)
# Column Y
secondDerivatives = rep(0, XResolution)
# Column Z
centerlineCurvatures = c()

# Floodplain Model
# Column B
yRightWaves = c()
# Column C
yLeftWaves = c()
# Column E
yRightToe = c()
# Column F
zRightToe = c()
# Column H
yRightTop = c()
# Column I
zRightTop = c()
# Column K
yLeftToe = c()
# Column L
zLeftToe = c()
# Column N
yLeftTop = c()
# Column O
zLeftTop = c()

# XS Model
# Column D
b_s = c()
# Column F
k_s = c()
# Columns I-AC
h_n = matrix(nrow=XResolution, ncol=ChannelXSPoints)
# Columns AD-AX
n_xs = matrix(nrow=XResolution, ncol=ChannelXSPoints)
# Columns AY-BS
bankPoints = matrix(nrow=XResolution, ncol=ChannelXSPoints)
# Columns BT-CN
xShifts = matrix(nrow=XResolution, ncol=ChannelXSPoints)

# Covariance
# Column B
Wbf_stds = c()
# Column D
Zt_stds = c()
# Column H
CV_WZ = c()
# Column I
CV_ZC = c()

# Meander Models
# Langbein and Leopold
# Column B
disturbedDx = c(0)
# Column C
disturbedDy = c(0)
# Column E
disturbedThetas = c()
# Column F
disturbedX = c(0)
# Column G
disturbedY = c(0)

# Ferguson
# Column E
fergusonY = c(0, 0.25)

#################################
#### Miscellaneous Variables ####
#################################

dxi = length/XResolution
dxr = (dxi/length)*2*pi
confinementRatio = bankfullWidth/(FPWidth+terraceWidth+bankfullWidth)
ks = 6.1*medianSedimentSize
n = 0.034*(ks^(1/6))
positiveGCS = 0
negativeGCS = 0
posPercentGCS = 0
negPercentGCS = 0
ki = -1
incr = 1/floor(ChannelXSPoints/2)

# Necessary values to produce a random wave (Perlin function)
Mr = 4294967296
Ar = 1664525
Cr = 1
Zr = floor(runif(1)*Mr)

# Initial random values (Perlin function)
ga = random()
gb = random()

while(ki < 1+incr)
{
	k1 = c(k1, round(ki, digits=5))
	ki = ki + incr
}

if(ChannelXSPoints %% 2 == 0)
	k1 = k1[abs(k1) > 0]

if(bankfullWidthMin > bankfullWidth)
	stop("Minimum bankfull width is greater than base bankfull width. Program exit.")

print("Computing river properties...")

# B, C, D, E, H, I, J, K, L, N, P, S, T, U, V, W, X, Y, Z (CM), B, C (FM)
for(i in seq(from=1, to=XResolution, by=1))
{
	# Computation of (mostly) x-coordinates
	increments = c(increments, i-1)
	xrads = c(xrads, (i-1)*dxr)
	xms = c(xms, (increments[i]/XResolution)*length)
	channelMeanders = c(channelMeanders, evaluateFunctions(Mc_functions, c(xrads[i], xms[i], increments[i]), "M"))
	if(i >= 2)
	{
		if(i == 2)
			dscms = c(dscms, sqrt((channelMeanders[i]-channelMeanders[i-1])**2 + (xms[i]-xms[i-1])**2))
		dscms = c(dscms, sqrt((channelMeanders[i]-channelMeanders[i-1])**2 + (xms[i]-xms[i-1])**2))
		scms = c(scms, scms[i-1] + dscms[i])
	}

	scms_r = c(scms_r, 2*pi*scms[i]/length)

	# Computation of (mostly) y-coordinates
	yRightWaves = c(yRightWaves, evaluateFunctions(RightFP_functions, c(xrads[i], xms[i], increments[i]), "R"))
	yLeftWaves = c(yLeftWaves, evaluateFunctions(LeftFP_functions, c(xrads[i], xms[i], increments[i]), "L"))
	wbf_pfs = c(wbf_pfs, evaluateFunctions(Wbf_functions, c(scms_r[i], xms[i], increments[i]), "W"))
	if(wbf_pfs[i]*bankfullWidth+bankfullWidth >= bankfullWidthMin)
		bankfullWidths = c(bankfullWidths, wbf_pfs[i]*bankfullWidth + bankfullWidth)
	else
		bankfullWidths = c(bankfullWidths, bankfullWidthMin)
	bankfullWidths_L = c(bankfullWidths_L, -bankfullWidths[i]/2)
	bankfullWidths_R = c(bankfullWidths_R, bankfullWidths[i]/2)
	centerlineCurvature_pfs = c(centerlineCurvature_pfs, evaluateFunctions(Cs_functions, c(scms_r[i], xms[i], increments[i]), "E"))

	if(XS_shape == crossSectionalShapes[2])
	{
		firstDerivatives[i] = as.double(Cs_functions[2,2])*cos(as.double(Cs_functions[2,3])*scms_r[i] + as.double(Cs_functions[2,4]))
		secondDerivatives[i] = as.double(Cs_functions[2,2])*(-sin(as.double(Cs_functions[2,3])*scms_r[i] + as.double(Cs_functions[2,4])))
	}

	if(i == 1)
	{
		centerlineCurvatures = c(centerlineCurvatures, centerlineCurvature_pfs[i])
	}
	else
	{
		if(length(dxcmds) == 0)
			dxcmds = c(dxcmds, (xms[i]-xms[i-1])/dscms[i-1])
		if(length(dycmds) == 0)
			dycmds = c(dycmds, (channelMeanders[i]-channelMeanders[i-1])/dscms[i-1])
		dxcmds = c(dxcmds, (xms[i]-xms[i-1])/dscms[i])
		dycmds = c(dycmds, (channelMeanders[i]-channelMeanders[i-1])/dscms[i])
		centerlineCurvatures = c(centerlineCurvatures, centerlineCurvature_pfs[i]+secondDerivatives[i]/((1 + (firstDerivatives[i])**2)**(3/2)))
	}
}

maxCenterlineCurvature = abs(centerlineCurvatures)[which.max(abs(centerlineCurvatures))]*1.2
disturbedAmp = 110*pi/180
disturbedMeander = scms[length(scms)]
ds = 1

# Q, R (CM), D, F, I-AC, AD-AX, AY-BS, BT-CN (XM)
for(i in seq(from=1, to=XResolution, by=1))
{
	if(centerlineCurvatures[i] < 0)
		b_s = c(b_s, (0.5*(1-((abs(centerlineCurvatures[i]))/maxCenterlineCurvature))))
	else if(centerlineCurvatures[i] > 0)
		b_s = c(b_s, (0.5*(1+((centerlineCurvatures[i])/maxCenterlineCurvature))))
	else if(centerlineCurvatures[i] == 0)
		b_s = c(b_s, 0.5)

	if(centerlineCurvatures[i] < 0)
		k_s = c(k_s, (-log(2)/log(b_s[i])))
	else
		k_s = c(k_s, (-log(2)/log(1-b_s[i])))

	disturbedThetas = c(disturbedThetas, disturbedAmp*sin(2*pi*scms[i]/disturbedMeander))

	if(i != 1)
	{
		disturbedDx = c(disturbedDx, ds*cos(disturbedThetas[i]))
		disturbedDy = c(disturbedDy, ds*sin(disturbedThetas[i]))
		disturbedX = c(disturbedX, disturbedX[i-1]+disturbedDx[i])
		disturbedY = c(disturbedY, disturbedY[i-1]+disturbedDy[i])
	}
}

sinuosity = scms[length(scms)]/xms[length(xms)]
channelSlope = ((XResolution*sum(scms*centerlineCurvatures)-sum(scms)*sum(centerlineCurvatures))/
	(XResolution*sum(scms**2)-(sum(scms))**2)) + (valleySlope/sinuosity)
channelIntercept = ((sum(centerlineCurvatures)*sum((scms**2))-sum(scms)*sum(scms*centerlineCurvatures))/
	(XResolution*sum(scms**2)-(sum(scms))**2))
disturbedY = (disturbedY - disturbedY[which.max(disturbedY)]/2)
if(!userDefinedDepth)
	bankfullDepth = (165*medianSedimentSize*criticalShieldsStress)/channelSlope

widthToDepthRatio = bankfullWidth/bankfullDepth
Wbf_a1 = as.double(Wbf_functions[2,2])
Zt_a1 = as.double(Zt_functions[2,2])
Zt_f1 = as.double(Zt_functions[2,3])
#wr = bankfullWidth*Wbf_a1+bankfullWidth
#wp = -bankfullWidth*Wbf_a1+bankfullWidth
#hres = 2*bankfullDepth*Zt_a1-(pi*bankfullWidth*valleySlope/Zt_f1)

for(i in seq(from=1, to=XResolution, by=1))
{
	thalwegs = c(thalwegs, (bankfullDepth*(evaluateFunctions(Zt_functions, c(scms_r[i], xms[i], increments[i]), "T") + bankfullDepth)) + scms[i]*channelSlope + datum)
	if(i == 1)
		thalwegsNoSlope = c(thalwegsNoSlope, thalwegs[i])
	else
		thalwegsNoSlope = c(thalwegsNoSlope, thalwegs[i]-(scms[i]-scms[1])*channelSlope)
}

for(i in seq(from=1, to=XResolution, by=1))
{
	if(i == 1)
		topsofBank = c(topsofBank, thalwegsNoSlope[which.max(thalwegsNoSlope)] + bankfullDepth)
	else
		topsofBank = c(topsofBank, topsofBank[i-1]+(scms[i]-scms[i-1])*valleySlope)

	bankfullDepths = c(bankfullDepths, topsofBank[i] - thalwegs[i])

	# Produce the bank points along the channel meander
	for(j in seq(from=1, to=ChannelXSPoints, by=1))
	{
		n_xs[i,j] = k1[j]*bankfullWidths[i]/2
		bankPoints[i,j] = channelMeanders[i] + n_xs[i,j]*dxcmds[i]
		xShifts[i,j] = xms[i] - n_xs[i,j]*dycmds[i]
		h_n[i,j] = crossSection(XS_shape, i, j)
	}
}

# Width at location where depth is at maximum
wr = bankfullWidths[which.max(bankfullDepths)]
# Width at location where depth is at minimum
wp = bankfullWidths[which.min(bankfullDepths)]
# Bed location at max depth - Bed location at min depth
hres = thalwegsNoSlope[which.max(thalwegsNoSlope)] - thalwegsNoSlope[which.min(thalwegsNoSlope)]
hcrit = hres/((wr/wp)-1)
maxLength = which(bankPoints == max(bankPoints), arr.ind = TRUE)
minLength = which(bankPoints == min(bankPoints), arr.ind = TRUE)
maxRow = maxLength[1,1]
maxCol = maxLength[1,2]
minRow = minLength[1,1]
minCol = minLength[1,2]
maxRightBank = bankPoints[maxRow, maxCol]
minLeftBank = bankPoints[minRow, minCol]
maxRightToe = yRightWaves[which.max(yRightWaves)]
minLeftToe = yLeftWaves[which.min(yLeftWaves)]
minRightToe = yRightWaves[which.min(yRightWaves)]
maxLeftToe = yLeftWaves[which.max(yLeftWaves)]

# E, F, H, I, K, L, N, O (FM)
for(i in seq(from=1, to=XResolution, by=1))
{
	yRightToe = c(yRightToe, yRightWaves[i] + FPWidth/2 + maxRightBank - minRightToe)
	yLeftToe = c(yLeftToe, -yLeftWaves[i] - FPWidth/2 + minLeftBank + minLeftToe)
	zRightToe = c(zRightToe, topsofBank[i] + outerFPEdgeHeight)
	zLeftToe = c(zLeftToe, zRightToe[i])
	yRightTop = c(yRightTop, yRightToe[i] + terraceWidth/2)
	yLeftTop = c(yLeftTop, yLeftToe[i] - terraceWidth/2)
	zRightTop = c(zRightTop, zRightToe[i] + outerTerraceEdgeHeight)
	zLeftTop = c(zLeftTop, zRightTop[i])

	standardizedDepth = standardize(thalwegsNoSlope[i], mean(thalwegsNoSlope), sd(thalwegsNoSlope))
	standardizedWidth = standardize(bankfullWidths[i], mean(bankfullWidths), sd(bankfullWidths))
	standardizedCenterlineCurvature = standardize(centerlineCurvatures[i], mean(centerlineCurvatures), sd(centerlineCurvatures))
	Wbf_stds = c(Wbf_stds, standardizedWidth)
	Zt_stds = c(Zt_stds, standardizedDepth)
	CV_WZ = c(CV_WZ, Wbf_stds[i]*Zt_stds[i])
	CV_ZC = c(CV_ZC, Zt_stds[i]*standardizedCenterlineCurvature)
	currentGCS = standardizedDepth*standardizedWidth
	if(currentGCS > 0){
		positiveGCS = positiveGCS + 1
	}
	else if(currentGCS < 0){
		negativeGCS = negativeGCS + 1
	}
}

if(positiveGCS != 0 || negativeGCS != 0)
{
	negPercentGCS = 100*negativeGCS/(negativeGCS+positiveGCS)
	posPercentGCS = 100*positiveGCS/(negativeGCS+positiveGCS)
}

print("Computations complete.")

Graph_yRightTop = c(round(yRightToe[XResolution/2], digits=3), round(yRightTop[XResolution/2], digits=3))
Graph_zRightTop = c(round(zRightToe[XResolution/2], digits=3), round(zRightTop[XResolution/2], digits=3))

Graph_yLeftTop = c(round(yLeftToe[XResolution/2], digits=3), round(yLeftTop[XResolution/2], digits=3))
Graph_zLeftTop = c(round(zLeftToe[XResolution/2], digits=3), round(zLeftTop[XResolution/2], digits=3))

Graph_yRightToe = c(round(n_xs[XResolution/2, ChannelXSPoints], digits=3), round(yRightToe[XResolution/2], digits=3))
Graph_zRightToe = c(round(h_n[XResolution/2, ChannelXSPoints], digits=3), round(zRightToe[XResolution/2], digits=3))

Graph_yLeftToe = c(round(n_xs[XResolution/2, 1], digits=3), round(yLeftToe[XResolution/2], digits=3))
Graph_zLeftToe = c(round(h_n[XResolution/2, 1], digits=3), round(zLeftToe[XResolution/2], digits=3))

Graph_yRightBoundary = c(round(yRightTop[XResolution/2], digits=3), round(yRightTop[XResolution/2]+boundaryWidth, digits=3))
Graph_zRightBoundary = c(round(zRightTop[XResolution/2], digits=3), round(zRightTop[XResolution/2], digits=3))

Graph_yLeftBoundary = c(round(yLeftTop[XResolution/2], digits=3), round(yLeftTop[XResolution/2]-boundaryWidth, digits=3))
Graph_zLeftBoundary = c(round(zLeftTop[XResolution/2], digits=3), round(zLeftTop[XResolution/2], digits=3))

################
#### Graphs ####
################
# Notes for legend:
# - par(xpd = TRUE) allows legend outside of plot
# - inset controls positioning
# - lty sets length of legend lines
# - lwd sets thickness of legend lines
# - pt.cex assures the plot itself isn't modified
# - cex controls point/text size

# Produce the centerline curvature graph
png(filename=file.path(directory, file_outputs[1]), 10, 7.5, "in", res=100)
plot(main = "Centerline Curvature", round(scms, digits=3), round(centerlineCurvatures, digits=3),
	ylim = range(centerlineCurvatures[which.min(centerlineCurvatures)]-0.05,centerlineCurvatures[which.max(centerlineCurvatures)]+0.05),
	col = "darkblue", xlab = "S (meters)", ylab = "Elevation (meters)", cex = 0.75)
lines(round(scms, digits=3), round(centerlineCurvatures, digits=3),
	col = "darkblue")
dev.off()

print(paste(file_outputs[1], "generated."))

png(filename=file.path(directory, file_outputs[2]), 10, 7.5, "in", res=100)
plot(main = "Valley Section", round(n_xs[XResolution/2,], digits=3), round(h_n[XResolution/2,], digits=3),
	xlim = range(yLeftTop[which.min(yLeftTop)]-boundaryWidth, yRightTop[which.max(yRightTop)]+boundaryWidth),
	ylim = range(h_n[XResolution/2,which.min(h_n[XResolution/2,])],
		zRightTop[which.max(zRightTop)]),
	col = "darkblue", xlab = "Y (meters)", ylab = "Elevation (meters)", cex = 0.75)
lines(round(n_xs[XResolution/2,], digits=3), round(h_n[XResolution/2,], digits=3),
	col = "darkblue", lwd = 4)

# Plot valley floors
points(yRightToe[XResolution/2], zRightToe[XResolution/2], col = "chocolate4")
lines(Graph_yRightToe, Graph_zRightToe, col = "chocolate4", lwd = 4)

points(yLeftToe[XResolution/2], zLeftToe[XResolution/2], col = "chocolate4")
lines(Graph_yLeftToe, Graph_zLeftToe, col = "chocolate4", lwd = 4)

# Plot valley tops
points(yRightTop[XResolution/2], zRightTop[XResolution/2], col = "black")
lines(Graph_yRightTop, Graph_zRightTop, col = "black", lwd = 4)

points(yLeftTop[XResolution/2], zLeftTop[XResolution/2], col = "black")
lines(Graph_yLeftTop, Graph_zLeftTop, col = "black", lwd = 4)

# Plot boundary widths
points(yRightTop[XResolution/2]+boundaryWidth, zRightTop[XResolution/2], col = "darkorchid4")
lines(Graph_yRightBoundary, Graph_zRightBoundary, col = "darkorchid4", lwd = 4)

points(yLeftTop[XResolution/2]-boundaryWidth, zLeftTop[XResolution/2], col = "darkorchid4")
lines(Graph_yLeftBoundary, Graph_zLeftBoundary, col = "darkorchid4", lwd = 4)

par(xpd = TRUE)
legend("topright", inset = c(0, -0.13), c("Boundaries", "Terrace", "Floodplain", "Channel"),
	lty = c(1,1,1,1), lwd = c(4,4,4,4), col = c("darkorchid4", "black", "chocolate4", "darkblue"), cex = 0.75)
dev.off()

print(paste(file_outputs[2], "generated."))

# Produce the Geometric Covariance Structures graph
png(filename=file.path(directory, file_outputs[3]), 10, 7.5, "in", res=100)
plot(main = "Geometric Covariance Structures", round(xms, digits=3), round(CV_WZ, digits=3),
	ylim = range(min(CV_WZ[which.min(CV_WZ)]-0.5, CV_ZC[which.min(CV_ZC)]-0.5),max(CV_WZ[which.max(CV_WZ)]+0.5, CV_ZC[which.max(CV_ZC)]+0.5)),
	col = "forestgreen", xlab = "X (meters)", ylab = "Geometric Covariance", cex = 0.75)
lines(round(xms, digits=3), round(CV_WZ, digits=3),
	col = "forestgreen")
par(new = TRUE)
plot(round(xms, digits=3), round(CV_ZC, digits=3),
	ylim = range(min(CV_WZ[which.min(CV_WZ)]-0.5, CV_ZC[which.min(CV_ZC)]-0.5),max(CV_WZ[which.max(CV_WZ)]+0.5, CV_ZC[which.max(CV_ZC)]+0.5)),
	col = "darkred", axes = FALSE, xlab = "", ylab = "", cex = 0.75)
lines(round(xms, digits=3), round(CV_ZC, digits=3),
	col = "darkred")
par(xpd = TRUE)
legend("topright", inset = c(0, -0.11), c("C(Wbf*Zt)", "C(Zt*Cs)"),
	lty = c(1,1), lwd = c(4,4), col = c("forestgreen", "darkred"), cex = 1)
dev.off()

print(paste(file_outputs[3], "generated."))

# Produce the longitudinal profile graph
png(filename=file.path(directory, file_outputs[4]), 10, 7.5, units = "in", res=100)
plot(main = "Longitudinal Profile", round(xms, digits=3), round(zRightTop, digits=3),
	ylim = range(thalwegs[which.min(thalwegs)]-5,zRightTop[which.max(zRightTop)]+5),
	col = "black", xlab = "X (meters)", ylab = "Elevation (meters)", cex = 0.75)
lines(round(xms, digits=3), round(zRightTop, digits=3),
	col = "black")
par(new = TRUE)
plot(round(xms, digits=3), round(zRightToe, digits=3),
	ylim = range(thalwegs[which.min(thalwegs)]-5,zRightTop[which.max(zRightTop)]+5),
	col = "chocolate4", axes = FALSE, xlab = "", ylab = "", cex = 0.75)
lines(round(xms, digits=3), round(zRightToe, digits=3),
	col = "chocolate4")
par(new = TRUE)
plot(round(xms, digits=3), round(topsofBank, digits=3),
	ylim = range(thalwegs[which.min(thalwegs)]-5,zRightTop[which.max(zRightTop)]+5),
	col = "chartreuse4", axes = FALSE, xlab = "", ylab = "", cex = 0.75)
lines(round(xms, digits=3), round(topsofBank, digits=3),
	col = "chartreuse4")
par(new = TRUE)
plot(round(xms, digits=3), round(thalwegs, digits=3),
	ylim = range(thalwegs[which.min(thalwegs)]-5,zRightTop[which.max(zRightTop)]+5),
	col = "dimgray", axes = FALSE, xlab = "", ylab = "", cex = 0.75)
lines(round(xms, digits=3), round(thalwegs, digits=3),
	col = "dimgray")
par(xpd = TRUE)
legend("topright", inset = c(0, -0.13), c("Valley Top", "Valley Floor", "Bank Top", "Thalweg Elevation"),
	lty = c(1,1,1,1), lwd = c(4,4,4,4), col = c("black", "chocolate4", "chartreuse4", "dimgray"), cex = 0.75)
dev.off()

print(paste(file_outputs[4], "generated."))

# Produce the planform graph(s)
png(filename=file.path(directory, file_outputs[5]), 10, 7.5, units = "in", res=100)
plot(main = "Planform", round(xms, digits=3), round(channelMeanders, digits=3),
	ylim = range((yLeftTop[which.min(yLeftTop)]-5),(yRightTop[which.max(yRightTop)]+5)),
	col = "darkblue", xlab = "X (meters)", ylab = "Y (meters)", cex = 0.75)
lines(round(xms, digits=3), round(channelMeanders, digits=3),
	col = "darkblue")
par(new = TRUE)
plot(round(xms, digits=3), round(bankPoints[,ChannelXSPoints], digits=3),
	ylim = range((yLeftTop[which.min(yLeftTop)]-5),(yRightTop[which.max(yRightTop)]+5)),
	col = "chartreuse4", axes = FALSE, xlab = "", ylab = "", cex = 0.75)
lines(round(xms, digits=3), round(bankPoints[,ChannelXSPoints], digits=3),
	col = "chartreuse4")
par(new = TRUE)
plot(round(xms, digits=3), round(bankPoints[,1], digits=3),
	ylim = range((yLeftTop[which.min(yLeftTop)]-5),(yRightTop[which.max(yRightTop)]+5)),
	col = "chartreuse4", axes = FALSE, xlab = "", ylab = "", cex = 0.75)
lines(round(xms, digits=3), round(bankPoints[,1], digits=3),
	col = "chartreuse4")
par(new = TRUE)
plot(round(xms, digits=3), round(yRightToe, digits=3),
	ylim = range((yLeftTop[which.min(yLeftTop)]-5),(yRightTop[which.max(yRightTop)]+5)),
	col = "chocolate4", axes = FALSE, xlab = "", ylab = "", cex = 0.75)
lines(round(xms, digits=3), round(yRightToe, digits=3),
	col = "chocolate4")
par(new = TRUE)
plot(round(xms, digits=3), round(yLeftToe, digits=3),
	ylim = range((yLeftTop[which.min(yLeftTop)]-5),(yRightTop[which.max(yRightTop)]+5)),
	col = "chocolate4", axes = FALSE, xlab = "", ylab = "", cex = 0.75)
lines(round(xms, digits=3), round(yLeftToe, digits=3),
	col = "chocolate4")
par(new = TRUE)
plot(round(xms, digits=3), round(yRightTop, digits=3),
	ylim = range((yLeftTop[which.min(yLeftTop)]-5),(yRightTop[which.max(yRightTop)]+5)),
	col = "black", axes = FALSE, xlab = "", ylab = "", cex = 0.75)
lines(round(xms, digits=3), round(yRightTop, digits=3),
	col = "black")
par(new = TRUE)
plot(round(xms, digits=3), round(yLeftTop, digits=3),
	ylim = range((yLeftTop[which.min(yLeftTop)]-5),(yRightTop[which.max(yRightTop)]+5)),
	col = "black", axes = FALSE, xlab = "", ylab = "", cex = 0.75)
lines(round(xms, digits=3), round(yLeftTop, digits=3),
	col = "black")
par(xpd = TRUE)
legend("topright", inset = c(0, -0.13), c("Channel Meander", "Channel Banks", "Valley Floors", "Valley Tops"),
	lty = c(1,1,1,1), lwd = c(4,4,4,4), col = c("darkblue", "chartreuse4", "chocolate4", "black"), cex = 0.75)
dev.off()

print(paste(file_outputs[5], "generated."))

#png(filename="DisturbedMeander.png", 10, 7.5, "in", res=100)
#plot(main = "Disturbed Meander", round(disturbedX, digits=3), round(disturbedY, digits=3),
#	ylim = range(disturbedY), col="chartreuse4", xlab = "X (meters)", ylab = "Y (meters)", cex = 0.75)
#lines(round(disturbedX, digits=3), round(disturbedY, digits=3), col="chartreuse4")
#dev.off()

#####################
#### CSV OUTPUTS ####
#####################
# X = xShifts + xms + xms + xms + xms + xms + xms
# Y = bankPoints + yRightTop + yLeftTop + (0.5 + yRightTop[which.max(yRightTop)]) + -(0.5 + yRightTop[which.max(yRightTop)]) + yLeftToe + yRightToe
# Z = h_n + zRightTop + zLeftTop + zRightTop + zRightTop + zLeftToe + zRightToe

# Produce BoundaryPoints.csv
values = data.frame(matrix(nrow=17, ncol=1), stringsAsFactors=FALSE)
values[1,1] = XResolution*(ChannelXSPoints+2)
values[2,1] = XResolution*ChannelXSPoints
values[3,1] = XResolution*(ChannelXSPoints+5)
values[4,1] = XResolution*(ChannelXSPoints-1)
values[5,1] = 0
values[6,1] = XResolution*(ChannelXSPoints+4)
values[7,1] = XResolution*(ChannelXSPoints+1)
values[8,1] = XResolution*(ChannelXSPoints+3)
values[9,1] = XResolution*(ChannelXSPoints+4)-1
values[10,1] = XResolution*(ChannelXSPoints+2)-1
values[11,1] = XResolution*(ChannelXSPoints+5)-1
values[12,1] = XResolution-1
values[13,1] = XResolution*ChannelXSPoints-1
values[14,1] = XResolution*(ChannelXSPoints+6)-1
values[15,1] = XResolution*(ChannelXSPoints+1)-1
values[16,1] = XResolution*(ChannelXSPoints+3)-1
values[17,1] = XResolution*(ChannelXSPoints+2)

write.table(values, file = file.path(directory, file_outputs[6]),
	append = FALSE, row.names = FALSE, col.names = FALSE, quote = FALSE)

print(paste(file_outputs[6], "generated."))

# Produce Data.csv
values = data.frame(matrix(nrow=14, ncol=1), stringsAsFactors=FALSE)
rownames(values) = c("Coefficient of Variation (Wbf):", "Standard Deviation (Wbf):", "Average (Wbf):",
		"Coefficient of Variation (Hbf):", "Standard Deviation (Hbf):", "Average (Hbf):",
		"wr:", "wp:", "hres:", "hcrit:", "GCS (-):", "GCS (+):", "Sinuosity:", "Channel Slope:")
values[1,1] = c(round(sd(bankfullWidths)/mean(bankfullWidths), digits=3))
values[2,1] = c(round(sd(bankfullWidths), digits=3))
values[3,1] = c(round(mean(bankfullWidths), digits=3))
values[4,1] = c(round(sd(bankfullDepths)/mean(bankfullDepths), digits=3))
values[5,1] = c(round(sd(bankfullDepths), digits=3))
values[6,1] = c(round(mean(bankfullDepths), digits=3))
values[7,1] = c(round(wr, digits=3))
values[8,1] = c(round(wp, digits=3))
values[9,1] = c(round(hres, digits=3))
values[10,1] = c(round(hcrit, digits=3))
values[11,1] = c(paste(as.character(round(negPercentGCS, digits=3)), "%", sep=""))
values[12,1] = c(paste(as.character(round(posPercentGCS, digits=3)), "%", sep=""))
values[13,1] = c(round(sinuosity, digits=3))
values[14,1] = c(round(channelSlope, digits=5))
write.table(values, file = file.path(directory, file_outputs[7]),
	append = FALSE, col.names = FALSE, sep = "\t", quote = FALSE)

print(paste(file_outputs[7], "generated."))

# Produce CartesianCoordinates.csv
header1 = data.frame("X,Y,Z")
header2 = data.frame("X,Y")
header3 = data.frame("X,Z")
header4 = data.frame("Y,Z")

firstSet = data.frame(rbind(c(format(round(xShifts[1,1], 6), nsmall=6),
		format(round(bankPoints[1,1], 6), nsmall=6), format(round(h_n[1,1], 6), nsmall=6))))
points = data.frame()

for(j in seq(from=1, to=ChannelXSPoints, by=1))
	for(i in seq(from=1, to=XResolution, by=1))
		if(i != 1 || j != 1)
			points = rbind(points, c(round(xShifts[i,j], digits=3), round(bankPoints[i,j], digits=3), round(h_n[i,j], digits=3)))

for(i in seq(from=1, to=XResolution, by=1))
	points = rbind(points, c(round(xms[i], digits=3), round(yRightTop[i], digits=3), round(zRightTop[i], digits=3)))

for(i in seq(from=1, to=XResolution, by=1))
	points = rbind(points, c(round(xms[i], digits=3), round(yLeftTop[i], digits=3), round(zLeftTop[i], digits=3)))

for(i in seq(from=1, to=XResolution, by=1))
	points = rbind(points, c(round(xms[i], digits=3), round(boundaryWidth + yRightTop[which.max(yRightTop)], digits=3), round(zRightTop[i], digits=3)))

for(i in seq(from=1, to=XResolution, by=1))
	points = rbind(points, c(round(xms[i], digits=3), round(-boundaryWidth - yRightTop[which.max(yRightTop)], digits=3), round(zRightTop[i], digits=3)))

for(i in seq(from=1, to=XResolution, by=1))
	points = rbind(points, c(round(xms[i], digits=3), round(yLeftToe[i], digits=3), round(zLeftToe[i], digits=3)))

for(i in seq(from=1, to=XResolution, by=1))
	points = rbind(points, c(round(xms[i], digits=3), round(yRightToe[i], digits=3), round(zRightToe[i], digits=3)))

write.table(header1, file=file.path(directory, file_outputs[8]), row.names=FALSE, col.names=FALSE, quote=FALSE, append=TRUE)
write.table(firstSet, file=file.path(directory, file_outputs[8]), row.names=FALSE, col.names=FALSE, quote=FALSE, sep=",", append=TRUE)
write.table(points, file=file.path(directory, file_outputs[8]), row.names=FALSE, col.names=FALSE, sep= ",", append=TRUE)
print(paste(file_outputs[8], "generated."))

points = data.frame()

for(i in seq(from=1, to=XResolution, by=1))
	points = rbind(points, c(round(scms[i], digits=3), round(centerlineCurvatures[i], digits=3)))

write.table(header2, file=file.path(directory, file_outputs[9]), row.names=FALSE, col.names=FALSE, quote=FALSE, append=TRUE)
write.table(points, file=file.path(directory, file_outputs[9]), row.names=FALSE, col.names=FALSE, sep= ",", append=TRUE)
print(paste(file_outputs[9], "generated."))

points = data.frame()

for(i in seq(from=1, to=ChannelXSPoints, by=1))
	points = rbind(points, c(round(n_xs[XResolution/2,i], digits=3), round(h_n[XResolution/2,i], digits=3)))

points = rbind(points, c(round(yRightTop[XResolution/2]+boundaryWidth, digits=3), round(zRightTop[XResolution/2], digits=3)))
points = rbind(points, c(round(yLeftTop[XResolution/2]-boundaryWidth, digits=3), round(zLeftTop[XResolution/2], digits=3)))
points = rbind(points, c(round(yRightTop[XResolution/2], digits=3), round(zRightTop[XResolution/2], digits=3)))
points = rbind(points, c(round(yRightToe[XResolution/2], digits=3), round(zRightToe[XResolution/2], digits=3)))
points = rbind(points, c(round(yLeftTop[XResolution/2], digits=3), round(zLeftTop[XResolution/2], digits=3)))
points = rbind(points, c(round(yLeftToe[XResolution/2], digits=3), round(zLeftToe[XResolution/2], digits=3)))

write.table(header4, file=file.path(directory, file_outputs[10]), row.names=FALSE, col.names=FALSE, quote=FALSE, append=TRUE)
write.table(points, file=file.path(directory, file_outputs[10]), row.names=FALSE, col.names=FALSE, sep= ",", append=TRUE)
print(paste(file_outputs[10], "generated."))

points = data.frame()

for(i in seq(from=1, to=XResolution, by=1))
	points = rbind(points, c(round(xms[i], digits=3), round(CV_WZ[i], digits=3)))

for(i in seq(from=1, to=XResolution, by=1))
	points = rbind(points, c(round(xms[i], digits=3), round(CV_ZC[i], digits=3)))

write.table(header2, file=file.path(directory, file_outputs[11]), row.names=FALSE, col.names=FALSE, quote=FALSE, append=TRUE)
write.table(points, file=file.path(directory, file_outputs[11]), row.names=FALSE, col.names=FALSE, sep= ",", append=TRUE)
print(paste(file_outputs[11], "generated."))

points = data.frame()

for(i in seq(from=1, to=XResolution, by=1))
	points = rbind(points, c(round(xms[i], digits=3), round(zRightTop[i], digits=3)))

for(i in seq(from=1, to=XResolution, by=1))
	points = rbind(points, c(round(xms[i], digits=3), round(zRightToe[i], digits=3)))

for(i in seq(from=1, to=XResolution, by=1))
	points = rbind(points, c(round(xms[i], digits=3), round(thalwegs[i], digits=3)))

for(i in seq(from=1, to=XResolution, by=1))
	points = rbind(points, c(round(xms[i], digits=3), round(topsofBank[i], digits=3)))

write.table(header3, file=file.path(directory, file_outputs[12]), row.names=FALSE, col.names=FALSE, quote=FALSE, append=TRUE)
write.table(points, file=file.path(directory, file_outputs[12]), row.names=FALSE, col.names=FALSE, sep= ",", append=TRUE)
print(paste(file_outputs[12], "generated."))

points = data.frame()

for(i in seq(from=1, to=XResolution, by=1))
	points = rbind(points, c(round(xms[i], digits=3), round(channelMeanders[i], digits=3)))

for(i in seq(from=1, to=XResolution, by=1))
	points = rbind(points, c(round(xms[i], digits=3), round(bankPoints[i,ChannelXSPoints], digits=3)))

for(i in seq(from=1, to=XResolution, by=1))
	points = rbind(points, c(round(xms[i], digits=3), round(bankPoints[i,1], digits=3)))

for(i in seq(from=1, to=XResolution, by=1))
	points = rbind(points, c(round(xms[i], digits=3), round(yRightTop[i], digits=3)))

for(i in seq(from=1, to=XResolution, by=1))
	points = rbind(points, c(round(xms[i], digits=3), round(yLeftTop[i], digits=3)))

for(i in seq(from=1, to=XResolution, by=1))
	points = rbind(points, c(round(xms[i], digits=3), round(yRightToe[i], digits=3)))

for(i in seq(from=1, to=XResolution, by=1))
	points = rbind(points, c(round(xms[i], digits=3), round(yLeftToe[i], digits=3)))

write.table(header2, file=file.path(directory, file_outputs[13]), row.names=FALSE, col.names=FALSE, quote=FALSE, append=TRUE)
write.table(points, file=file.path(directory, file_outputs[13]), row.names=FALSE, col.names=FALSE, sep= ",", append=TRUE)
print(paste(file_outputs[13], "generated."))

print("Done.")

}
