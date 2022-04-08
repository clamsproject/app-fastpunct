"""examples.py

Some examples for testing and eyeballing parts of the code.

"""

# This is an example segment where fastpunct inserts repetition into the string

segment_with_duplicates_in = """judy woodruff after the news summary the twa bombing is once again our major focus tonight first israeli prime minister peres says who he thinks is to blame then we hear from a reporter who just returned from europe and the mideast finding out how the terrorists operate and from an airline safety expert we next move on to a sampling of what some astronauts had to say at today's shuttle disaster hearing finally a documentary report on what's being done to protect airliners from a killer called wind shear.news summary"""

segment_with_duplicates_out = """Judy Woodruff after the news summary: "The TWA bombing is once again our major focus tonight first Israeli Prime Minister Peres says who he thinks is to blame then we hear from a reporter who just returned from Europe and the Mideast finding out how the terrorists operate and from an airline safety expert we next move on to a sampling of what some astronauts had to say at today's shuttle disaster hearing finally a documentary report on what's being done to protect airliners from a killer called Wind Shear.news summary: "After the news summary: The TWA bombing is once again our major focus tonight first Israeli Prime Minister Peters: "First Israeli Prime Minister Peres says who he thinks is to blame then we hear from a reporter who just returned from Europe and the mideast finding out how the terrorists operate and from an airline safety expert we next move on to a sampling of what some astronauts had to say at today's shuttle disaster hearing finally a documentary report on what some astronaut"""


# Some cached results from prior invocations of fastpunct so we can run the code
# quickly with loading all the libraries and running the slow code.

cached_results = {

    'been':
    'Been.',

    "evening i'm jim lehrer on the newshour tonight phil ponce likes of the us military reservist call up what it means and who's affected senator attacked and urban debate new post colorado gun control proposals charles krauss tells the story of brazil's economic crisis and rebound and poet laureate robert pinsky reason ben johnson paul all on children and tragedy and all follows a summary that is this tuesday":
    "Evening I'm Jim Lehrer on the newshour tonight, Phil Ponce, likes of the U.S. military reservist, call up what it means and who's affected senator attacked and urban debate new post Colorado gun control proposals, Charles Krauss tells the story of Brazil's economic crisis and rebound and poet Laurent Pinsky reason Ben Johnson Paul All on Children and Tragicity and All follows a summary that is this Tuesday.",

    'keating the world is the biggest challenge of the new century which is widely condemned promote satellite technology to help the american farmer be even more connected':
    'Keating the world is the biggest challenge of the new century, which is widely condemned promote satellite technology to help the American farmer be even more connected.',

    'the world':
    'The world.',

    "by the corporation for public broadcasting and by the annual financial support from viewers like you president clinton authorized the pentagon today to call up more than thirty thousand reserve and national guard personnel they'll be used in the air campaign over kosovo and the three g i've captured by a bizarre troops were pronounced dead by red cross doctor as bagels bombing of serbia and the flight of ethnic albanian refugees from kosovo continue on beer narrates our update report":
    "By the Corporation for Public Broadcasting and by the annual financial support from viewers like you, President Clinton authorized the Pentagon today to call up more than thirty thousand Reserve and National Guard personnel they'll be used in the air campaign over Kosovo and the three G I've captured by a bizarre troops were pronounced dead by Red Cross doctor as Bagels bombing of Serbia and the flight of ethnic Albanian refugees from Kosovo continue on beer narrates, our update report."

}

