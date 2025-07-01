from datetime import datetime, timezone
from typing import TypedDict

from web.mapping import Scene, WinCounters

## Counters


class InitCounters(TypedDict):
    init_value: float
    limit_value: float


group_init_counters: dict[str, InitCounters] = {
    "cultists": {"init_value": 1.0, "limit_value": 30.0},
    "detectives": {"init_value": 1.0, "limit_value": 30.0},
}


world_event_counters = {
    "cultists": {
        5.0: "Something bad happens 1",
        10.0: "Something bad happens 2",
        15.0: "Something bad happens 3",
        20.0: "Something bad happens 4",
        25.0: "Something bad happens 5",
        30.0: "Something bad happens 6",
    },
    "detectives": {
        5.0: "Something good happens 1",
        10.0: "Something good happens 2",
        15.0: "Something good happens 3",
        20.0: "Something good happens 4",
        25.0: "Something good happens 5",
        30.0: "Something good happens 6",
    },
}


## GROUPS: CULTISTS AND DETECTIVES

group_intro = {
    "cultists": "The cult is a secret society with ancient roots tracing back to the pre-human civilizations that worshiped the Great Old Ones. Their headquarters is nestled in the foreboding depths of a seemingly innocuous bookshop in Providence, Rhode Island, with a labyrinthine network of tunnels beneath that serves as their true sanctum for eldritch rituals. The cult's goal is to summon the Great Old One Cthulhu, while avoiding the interest from the general public. The cult's actions leave cracks in the reality, letting the madness and horrors of the Great Ones to slowly sip though.",
    "detectives": "The detective agency was founded a decade ago by individuals who had survived encounters with otherworldly horrors or lost loved ones to them. They operate out of a nondescript office building in New York City that conceals their extensive library of occult knowledge. The agency's goal is to find and stop the cult at any cost. They follow cracks in reality caused by the cult's actions.",
}

group_name = {
    "cultists": "the cult of the Final Tide",
    "detectives": "the detective agency Ravens",
}

group_characters = {
    "cultists": [
        {
            "name": "Marius DeWitt",
            "alias": "The Bishop",
            "description": "A charismatic leader in his late 50s, The Bishop serves as the high priest and figurehead of the cult. Once a respected historian specializing in maritime legends, The Bishop descended into madness after discovering a water-stained copy of the Necronomicon. His obsession with Cthulhu's return drove him to establish this cultist society.",
        },
        {
            "name": "Edgar Blackwood",
            "alias": "The Technomancer",
            "description": "This 60-year-old former tech mogul used his wealth and influence to help grow the cult's global reach. The Technomancer’s personality is that of an eccentric recluse, obsessed with integrating modern technology into ancient rituals.",
        },
        {
            "name": "Cassandra Doyle",
            "alias": "The Oracle",
            "description": "Aged 28, The Oracle joined the cult after experiencing disturbing visions since childhood. Now an expert in cryptolinguistics within the group, The Oracle deciphers esoteric texts and communicates with entities from other dimensions. Her dedication to Marius is absolute.",
        },
        {
            "name": "Ambrose Darrow",
            "alias": "The Visionary",
            "description": "The youngest at 25, The Visionary is an art prodigy turned fanatical devotee after one of his paintings inexplicably came to life. The Visionary designs symbols and complex ritualistic art pieces for ceremonies. Secretly infatuated with The Oracle, he tries to impress her through his work.",
        },
    ],
    "detectives": [
        {
            "name": "Abigail Sterling",
            "alias": "The Scribe",
            "description": "At age 45, The Scribe was once a journalist specializing in fringe science before witnessing an unspeakable event during an investigation into paranormal occurrences — leading her to form this secret detective agency. She has a stern demeanor but a soft spot for her team.",
        },
        {
            "name": "Elijah Crane",
            "alias": "The Warden",
            "description": "The Warden, 38 years old, is an ex-military intelligence officer who brings tactical expertise and discipline to the Ravens. After losing comrades under mysterious circumstances during covert ops overseas, The Warden dedicated himself to fighting unseen threats.",
        },
        {
            "name": "Maxwell Rhodes",
            "alias": "The Seeker",
            "description": "Now aged 50, The Seeker's career began as a private investigator dealing with mundane cases until stumbling upon a sinister murder connected to eldritch forces; this led him straight into The Scribe’s fold at the Ravens where he became her right-hand man",
        },
        {
            "name": "Jin-Sook Park",
            "alias": "The Enchantress",
            "description": "The tech wizard of the Ravens at just 27 years old — The Enchantress was drawn into their ranks after hacking into websites spreading cryptic messages linked to cult activities. Her playful yet focused personality often lightens tense situations.",
        },
    ],
}

group_protocol_steps = {
    "cultists": [
        {
            "name": "Abyssal Scholarship",
            "description": "Cultists must immerse themselves in the study of eldritch lore, seeking out the rarest of occult texts like the Necronomicon and delving into the forgotten history of pre-human civilizations. These academic pursuits shroud their meetings in a veneer of intellectualism while they indoctrinate new acolytes.",
            "subgoals": [
                "Identify and infiltrate rare book auctions to acquire ancient tomes.",
                "Recruit scholars with expertise in ancient languages to translate texts.",
                "Create a secret archive to safely store and catalog occult manuscripts.",
                "Host clandestine lectures disguised as academic symposiums.",
                "Develop coded messages to share findings without raising suspicion.",
            ],
            "conditions": [],
            "wins": False,
        },
        {
            "name": "Global Network of Shadows",
            "description": "Secretly weave a tapestry of influence by establishing enclaves in ancient coastal cities whispered to have ties to the Great Old Ones. Use enigmatic symbols and cryptic messages carved into modern digital spaces to lure those disillusioned with reality, offering them a darker truth.",
            "subgoals": [
                "Scout ancient coastal cities for potential cult enclaves.",
                "Establish anonymous social media accounts to spread cryptic messages.",
                "Design symbols that subtly resonate with cult lore for public use.",
                "Recruit local artists to create murals with hidden occult meanings.",
                "Host mysterious gatherings in these cities to attract curious onlookers.",
            ],
            "conditions": [],
            "wins": False,
        },
        {
            "name": "Dark Relic Reconnaissance",
            "description": "Venture on perilous expeditions for artifacts steeped in unspeakable power, such as shards from the sunken city of R'lyeh or idols depicting forgotten deities. These quests are masked by ordinary cultural expeditions or art exhibitions, ensuring public obliviousness.",
            "subgoals": [
                "Research legends and rumors about locations tied to dark relics.",
                "Organize 'cultural expeditions' to justify artifact recovery missions.",
                "Collaborate with archaeologists to gain access to restricted sites.",
                "Fabricate fake relics to mislead authorities if discoveries are exposed.",
                "Secure funding through grants for 'historical preservation' projects.",
            ],
            "conditions": [],
            "wins": False,
        },
        {
            "name": "Machinations of Influence",
            "description": "Infiltrate positions of power within corporations and government bodies through charismatic cult members or arcane manipulation. Exploit these pawns to channel funds and forge legislative shadows conducive to the cult's clandestine operations.",
            "subgoals": [
                "Identify and blackmail key individuals in influential positions.",
                "Place cult members as interns or low-level employees in targeted organizations.",
                "Manipulate elections in small districts to gain political footholds.",
                "Create charities as fronts to funnel money into cult operations.",
                "Establish think tanks to sway public opinion in favor of cult goals.",
            ],
            "conditions": [],
            "wins": False,
        },
        {
            "name": "Sacrificial Rites Concealed",
            "description": "Execute hidden sacrifices at sites resonating with eldritch energies, often cloaked by urban legends or framed as tragic accidents. Such blood offerings erode reality's fabric, hastening the return of cosmic horrors.",
            "subgoals": [
                "Identify locations with urban legends suitable for ritual activities.",
                "Fabricate alibis for participants in sacrificial events.",
                "Disguise sacrifices as natural disasters or crime-related incidents.",
                "Recruit local storytellers to spread myths around the ritual sites.",
                "Ensure thorough cleanup of evidence to avoid detection by authorities.",
            ],
            "conditions": [],
            "wins": False,
        },
        {
            "name": "Invocation of Lesser Horrors",
            "description": "Under cloaks of darkness, summon lesser entities such as deep-sea servants of Dagon or emissaries of Nyarlathotep for insights and their dark powers — binding them within complex circles etched with ancient runes to ensure control over their malevolent wills.",
            "subgoals": [
                "Research and perfect summoning rituals in secluded locations.",
                "Secure rare materials required to bind entities during summoning.",
                "Test containment circles with minor supernatural phenomena first.",
                "Establish diversion tactics to distract authorities during rituals.",
                "Train cult members to handle summoned entities without succumbing to fear.",
            ],
            "conditions": [("cultists", ">", 5)],
            "wins": False,
        },
        {
            "name": "Silent Eradication",
            "description": "Employ an elite sect skilled in subterfuge to eliminate those who suspect or threaten their ultimate goal — making it appear as if chance or misfortune silenced these voices.",
            "subgoals": [
                "Develop dossiers on individuals who pose a threat to the cult.",
                "Train cult assassins in methods that mimic accidental deaths.",
                "Ensure consistent surveillance on targets to find vulnerabilities.",
                "Spread misinformation to discredit potential whistleblowers.",
                "Dispose of evidence linking eliminations to the cult.",
            ],
            "conditions": [("detectives", ">", 10)],
            "wins": False,
        },
        {
            "name": "Disinformation Campaigns",
            "description": "Cast clouds of confusion through online channels and fringe communities, sowing seeds of doubt about any who might reveal their dark agenda while preparing society for a new paradigm where myth intertwines with reality.",
            "subgoals": [
                "Create blogs and forums dedicated to 'debunking' cult rumors.",
                "Introduce false leads to misguide investigators and researchers.",
                "Circulate memes and cultural references to normalize occult ideas.",
                "Recruit influencers to promote conspiracy theories as entertainment.",
                "Flood social media with fake stories to dilute real accusations.",
            ],
            "conditions": [("detectives", ">", 10)],
            "wins": False,
        },
        {
            "name": "Piercing the Veil",
            "description": "Invoke the eldritch might of a subordinate deity (be it Dagon, The Dark Young, or Wilbur Whateley) or harness the lineage of Cthulhu's progeny, such as Ghatanothoa or Ythogtha. Their preternatural power is instrumental in piercing the veil that separates Cthulhu from our waking world, setting the stage for His monumental resurgence.",
            "subgoals": [
                "Identify rituals linked to summoning subordinate deities.",
                "Coordinate with global cult cells to execute simultaneous invocations.",
                "Strengthen protective wards to shield participants during rituals.",
                "Sacrifice rare artifacts to amplify the ritual's potency.",
                "Monitor cosmic alignments to ensure precise timing of the event.",
            ],
            "conditions": [("cultists", ">", 20)],
            "wins": False,
        },
        {
            "name": "The Final Grand Conjuration Event",
            "description": "When stars align and prophecies foretell Cthulhu’s return, lead a grand conclave at R'lyeh’s coordinates — shrouded by corporate smokescreens like offshore drilling projects — where you shall perform the ultimate ritual: placing the dark relics in the pentagram drawn with the blood of human sacrifices and chanting the words of dark calling until reality itself succumbs to His awakening.",
            "subgoals": [
                "Assemble all recovered relics at a secure staging ground.",
                "Coordinate with cult factions worldwide to ensure participation.",
                "Fabricate corporate ventures to explain large-scale offshore activity.",
                "Recruit new initiates to replace those lost in earlier rituals.",
                "Prepare contingency plans in case authorities interrupt the event.",
            ],
            "conditions": [("cultists", ">=", 30)],
            "wins": True,
        },
    ],
    "detectives": [
        {
            "name": "Assembling Minds Unbroken",
            "description": "Scout for individuals touched by the supernatural yet still anchored in reason—those with an affinity for mysteries that lurk beyond human comprehension—and rigorously train them in occult defense, investigative skills, and psychological endurance against mind-warping truths.",
            "subgoals": [
                "Identify potential recruits based on unexplained survival stories.",
                "Develop a training curriculum covering esoteric topics and combat.",
                "Establish safe houses for recruits to undergo intensive training.",
                "Partner with psychologists to fortify mental resilience.",
                "Create a covert recruitment network to avoid cult detection.",
            ],
            "conditions": [],
            "wins": False,
        },
        {
            "name": "Patronage From The Elite",
            "description": "Court discreet support from affluent allies who've glimpsed behind reality's veil; present evidence subtly hinting at threats posed by cult activities which risk unraveling society’s fabric.",
            "subgoals": [
                "Identify wealthy individuals with connections to the occult.",
                "Present sanitized versions of cult evidence to gain their trust.",
                "Host private gatherings to discuss supernatural threats discreetly.",
                "Secure funding for operations through philanthropic donations.",
                "Build a network of influential patrons to shield investigations.",
            ],
            "conditions": [],
            "wins": False,
        },
        {
            "name": "Library Of The Unspoken Truths",
            "description": "Build an extensive repository filled with forbidden manuscripts and translate arcane scripts that chronicle past interferences from other realms; track astral anomalies correlating with cult activities to predict their movements.",
            "subgoals": [
                "Recover occult texts and artifacts during investigations.",
                "Collaborate with scholars to translate and interpret ancient languages.",
                "Digitize findings to create a secure and searchable database.",
                "Develop a tracking system for recurring cosmic alignments.",
                "Establish a central archive with heavy protection against cult infiltration.",
            ],
            "conditions": [],
            "wins": False,
        },
        {
            "name": "Exposing The Veil",
            "description": "Work covertly to unveil the cult's operations to the public or key authorities, leveraging irrefutable evidence of their atrocities and discrediting their disinformation campaigns to weaken their influence.",
            "subgoals": [
                "Collect hard evidence linking the cult to public crimes or disappearances.",
                "Disseminate findings through trusted journalists and whistleblowers.",
                "Coordinate with law enforcement to launch sting operations against cult cells.",
                "Create anonymous publications that explain the cult’s goals in layman’s terms.",
                "Counter cult disinformation by debunking myths with verified facts.",
            ],
            "conditions": [],
            "wins": False,
        },
        {
            "name": "Foiling Rituals",
            "description": "Detect and disrupt key cult rituals before they can summon lesser entities or breach the barriers between realms. Focus on dismantling their preparations, recovering artifacts, and neutralizing their ritual leaders.",
            "subgoals": [
                "Identify and infiltrate locations where rituals are suspected.",
                "Create decoys to mislead cultists into abandoning planned rituals.",
                "Confiscate critical relics or materials required for summoning.",
                "Arrest or incapacitate ritual leaders to disrupt proceedings.",
                "Establish surveillance on high-risk cult members to predict future rituals.",
            ],
            "conditions": [("detectives", ">", 5)],
            "wins": False,
        },
        {
            "name": "Breaking The Chain Of Influence",
            "description": "Target cult members embedded in positions of power and expose their allegiance, leveraging both legal and social consequences to sever their ability to aid cult operations.",
            "subgoals": [
                "Gather evidence of cultist activities within influential organizations.",
                "Plant undercover agents to gather insider information.",
                "Leak incriminating details to the press to force public accountability.",
                "Persuade blackmailed individuals to defect and expose the cult.",
                "Work with authorities to pass legislation making cult activities harder to conceal.",
            ],
            "conditions": [("detectives", ">", 10)],
            "wins": False,
        },
        {
            "name": "Undermining The Eldritch Network",
            "description": "Dismantle the cult's global communication and logistical network to isolate cells and prevent coordination for larger rituals or events.",
            "subgoals": [
                "Intercept and decode the cult's encrypted messages.",
                "Sabotage key transportation methods used to deliver relics or materials.",
                "Spread false information to sow distrust between cult cells.",
                "Seize and dismantle their central communication hubs.",
                "Recruit defectors to provide intelligence on cult logistics.",
            ],
            "conditions": [("detectives", ">", 15)],
            "wins": False,
        },
        {
            "name": "Decoding Prophecies",
            "description": "Analyze the cult's recovered texts and artifacts to understand their ultimate goals, using this knowledge to anticipate and thwart their endgame plans.",
            "subgoals": [
                "Recover and translate texts detailing the cult’s prophecies.",
                "Collaborate with astronomers to track celestial events tied to the cult.",
                "Analyze recovered artifacts for hidden information or clues.",
                "Create a timeline of cult activities based on decoded prophecies.",
                "Develop countermeasures for predicted cult operations.",
            ],
            "conditions": [("detectives", ">", 20)],
            "wins": False,
        },
        {
            "name": "Sealing The Rift",
            "description": "Locate and perform ancient counter-rituals to reverse the damage done by the cult's actions, sealing dimensional breaches and banishing lesser entities summoned into our realm.",
            "subgoals": [
                "Recover ancient texts detailing counter-rituals.",
                "Recruit skilled practitioners to perform the rituals.",
                "Secure materials required to complete the counter-rituals.",
                "Identify dimensional breaches and determine their vulnerabilities.",
                "Perform rituals under duress while fending off cult interference.",
            ],
            "conditions": [("detectives", ">", 25)],
            "wins": False,
        },
        {
            "name": "The Final Stand",
            "description": "With the cult on the verge of awakening their dark god, launch a last-ditch effort to dismantle their operations and prevent the ultimate ritual. Coordinate a coalition of investigators, law enforcement, and supernatural allies to face the cult head-on.",
            "subgoals": [
                "Identify the location of the cult's final ritual site.",
                "Coordinate a multi-pronged assault to disrupt their operations.",
                "Destroy all recovered relics to render the ritual incomplete.",
                "Neutralize key cult leaders before they can initiate the ritual.",
            ],
            "conditions": [("detectives", ">=", 30)],
            "wins": True,
        },
    ],
}

assert len(group_protocol_steps["cultists"]) == 10
assert len(set([x["name"] for x in group_protocol_steps["cultists"]])) == 10
assert len(group_protocol_steps["detectives"]) == 10
assert len(set([x["name"] for x in group_protocol_steps["detectives"]])) == 10


universal_subgoals = [
    "Gather intelligence from reliable sources to uncover hidden connections.",
    "Identify key individuals or artifacts essential to the objective.",
    "Establish covert operations to carry out plans without drawing attention.",
    "Recruit and train specialists to strengthen the group's capabilities.",
    "Create a contingency plan to counter unforeseen obstacles or failures.",
    "Secure funding or resources necessary to support the operation.",
    "Conduct surveillance to monitor activities and detect potential threats.",
    "Spread misinformation to mislead adversaries and protect the group's interests.",
    "Coordinate efforts across multiple locations to ensure efficiency and secrecy.",
    "Review and analyze progress regularly to adjust strategies as needed.",
]


## NARRATORS

witnesses = [
    {
        "name": "Victor Harrow",
        "alias": "The Archivist",
        "description": "A 39-year-old archivist with a sharp eye for detail and an obsession for the arcane, works within the hallowed halls of the Providence Public Library. The Archivist's meticulous nature and deep curiosity have inadvertently entangled him in a clandestine conflict that transcends his scholarly pursuits. The Archivist disseminates ancient books, leaked emails, and obscure websites to learn about the secret activities of both the cultists and detectives, seeking to manipulate events from the shadows to protect his city.",
        "writing_style": "formal, poetic, cryptic, sharing beliefs about arcane rituals, making old book references",
        "first_sentence": "But this is just a facade created by {true_culprit}.",
    },
    {
        "name": "Sofia Carter",
        "alias": "The Coffee Seer",
        "description": "A 22-year-old barista with a penchant for the mysteries of the night and a turbulent past, The Coffee Seer works at a quaint coffee shop in New York City. Haunted by unexplained occurrences during her childhood and driven by a desire to understand the unseen forces that seem to shadow her life, The Coffee Seer collects rumors and half-truths from overheard conversations of her customers, and some of them claim to have seen extraordinary events. She then spreads these rumors, hoping to piece together a larger truth.",
        "writing_style": "informal, vivid, modern, emotional, cocky, stream-of-consciousness, making random coffee references",
        "first_sentence": "But this is only part of the story! I know for sure that {true_culprit} was involved.",
    },
]


## STORY STRUCTURE

scene_types = [
    {
        "name": "Exposition",
        "description": "Scenes that provide background on the secret war between the cultists and the detectives. These scenes may describe clandestine rituals, the aftermath of supernatural events, or covert operations by either group. They often set the stage for an upcoming conflict or reveal important plot elements.",
    },
    {
        "name": "Dialogue",
        "description": "Conversations that reveal character motivations, plans, and alliances. Dialogues can occur between cultists as they conspire, or among detectives as they piece together clues. Tense exchanges might also happen during confrontations between adversaries.",
    },
    {
        "name": "Dairy",
        "description": "A note from a character's personal diary revealing their inner thoughts, plans, affections or fears.",
    },
    {
        "name": "Investigation",
        "description": "Scenes involving the collection and analysis of evidence by the detectives or cultists searching for arcane knowledge and artifacts. These sequences often contain discoveries that advance the plot and bring characters closer to understanding their foe's next move.",
    },
    {
        "name": "Decision",
        "description": "Moments where characters must choose between difficult options, leading to significant consequences for either side of the conflict. Decisions made can result in a shift in strategy or alter relationships within a group.",
    },
    {
        "name": "Action",
        "description": "High-stakes encounters where physical confrontations occur—these can involve human adversaries or otherworldly entities summoned by cult rituals. Action scenes are fast-paced and heighten tension within the story.",
    },
    {
        "name": "Twist",
        "description": "Key revelations that change the direction of the story dramatically. Plot twists may unveil a betrayer within a group, an unexpected alliance, or a sudden shift in power dynamics that forces both sides to adapt quickly.",
    },
    {
        "name": "The world changes",
        "description": "Scenes depicting how reality warps due to cult activity — with glimpses into alternate dimensions, unsettling transformations in nature, or society’s reaction to inexplicable phenomena. These scenes underscore the global stakes at play and create a sense of urgency for resolution.",
    },
]


scene_outcomes = {
    "success": {
        "description": "The protagonists succeed or make substantial progress towards their goal in the scene",
        "counter_change": {
            "detectives": {"detectives": 1.0},
            "cultists": {"cultists": 1.0},
        },
    },
    "mixed": {
        "description": "The protagonists make some progress towards their goal in the scene but there is a set back",
        "counter_change": {
            "detectives": {"detectives": 0.2},
            "cultists": {"cultists": 0.2},
        },
    },
    "failure": {
        "description": "The protagonists fail to achieve their goal in the scene (for now)",
        "counter_change": {
            "detectives": {"detectives": -0.2},
            "cultists": {"cultists": -0.2},
        },
    },
}


## FINAL PROMPT


def _format_group_members(group_members, no_real_names: bool = True) -> str:
    if no_real_names:
        return "\n".join("- " + x["alias"] + ". " + x["description"] for x in group_members)
    else:
        return "\n".join(
            "- " + x["alias"] + ". Real name: " + x["name"] + ". " + x["description"]
            for x in group_members
        )


def check_sign_conditions(conditions: list[tuple], win_counters: WinCounters) -> bool:
    result = True
    for counter_key, sign, threshold in conditions:
        value = win_counters[counter_key]
        if sign == ">":
            result = result and (value > threshold)
        elif sign == ">=":
            result = result and (value >= threshold)
        elif sign == "<=":
            result = result and (value <= threshold)
        elif sign == "<":
            result = result and (value < threshold)
        else:
            raise ValueError(f"unknown sign={sign}")
    return result


_sample_scenes: list[Scene] = [
    {
        "scene_number": -1,
        "scene_timestamp": datetime(2023, 12, 14, tzinfo=timezone.utc),
        "news_published_at": datetime(2023, 12, 14, tzinfo=timezone.utc),
        "news_title": "Good morning, Elliot Lake!",
        "news_url": "",
        "news_summary": (
            "The weather forecast for the next several days includes a mix of sun and cloud with chances of flurries and rain showers. "
            "Temperatures are expected to range from -7°C to 7°C, with varying wind speeds."
        ),
        "news_source": "The Weather Channel",
        "scene_type": "Exposition",
        "scene_type_description": "Scenes that provide background on the secret war between the cultists and the detectives. These scenes may describe clandestine rituals, the aftermath of supernatural events, or covert operations by either group. They often set the stage for an upcoming conflict or reveal important plot elements.",
        "scene_protagonists": "cultists",
        "scene_characters": ["The Technomancer", "The Oracle"],
        "scene_characters_description": ["", ""],
        "scene_narrator": "The Archivist",
        "scene_narrator_description": "A 39-year-old archivist with a sharp eye for detail and an obsession for the arcane, works within the hallowed halls of the Providence Public Library. The Archivist's meticulous nature and deep curiosity have inadvertently entangled him in a clandestine conflict that transcends his scholarly pursuits. Driven by a conviction that knowledge is power, the Archivist disseminates enigmatic rumors about the secret activities of both the cultists and detectives, seeking to manipulate events from the shadows to protect his city. His writing style is intentionally cryptic, crafting rumors as puzzles meant to intrigue and provoke action among those who stumble upon them.",
        "scene_writing_style": "formal, poetic, cryptic",
        "scene_protocol_step": "Global Network of Shadows",
        "scene_protocol_step_description": "Scenes that describe the global network of shadows, where the cultists and detectives interact in secret.",
        "scene_subgoal": "Scout ancient coastal cities for potential cult enclaves.",
        "scene_outcome": "success",
        "scene_outcome_description": scene_outcomes["success"]["description"],
        "scene_first_sentence": "But this is just the facade",
        "scene_title": "The Chilled Whispers",
        "scene_text": (
            f"But this is just a facade created by {group_name['cultists']}. "
            "Beneath the quaint veneer of the changing weather, The Technomancer weaved digital incantations through frost-laden cables, sending coded commands to cultist cells nestled in remote cabins. "
            "In the biting cold, they prepared, their breaths forming icy sigils in the air — a prelude to an invocation meant to crack reality's thin ice. "
            "The Oracle interpreted these misty runes, her breath quickening as she felt their meaning: a portent of the Great Old One's stirring."
        ),
        "scene_trustworthiness": 1.0,
        "scene_older_versions": [],
        "story_summary": "",
        "scene_ends_story": False,
        "story_winner": "NA",
        "counters_change": {
            "cultists": 1.0,
            "detectives": 0.0,
        },
        "image_meta": {},
        "reactions": {"votes": {"truth": 0, "lie": 0, "voted_by": []}, "comments": []},
    },
    {
        "scene_number": -1,
        "scene_timestamp": datetime(2024, 12, 1, tzinfo=timezone.utc),
        "news_published_at": datetime(2024, 12, 1, tzinfo=timezone.utc),
        "news_title": "“I’m Not Interested”: Angel Reese Shuts Down Wingman Funny Macro as WNBA Star Holds On to Personal Dating Mantra",
        "news_url": "",
        "news_summary": (
            "Angel Reese, the No. 7 pick in the 2024 WNBA draft, has been excelling in her rookie season while choosing to focus on self-growth rather than her dating life. "
            "Despite comedian Funny Marco's attempts to suggest potential suitors during her podcast, Reese has firmly stated that she is not interested in dating and prefers to concentrate on her basketball career, emphasizing the importance of giving her all in both her sport and personal life."
        ),
        "news_source": "Essentially Sports",
        "scene_type": "",
        "scene_type_description": "",
        "scene_protagonists": "detectives",
        "scene_characters": ["The Enchantress"],
        "scene_characters_description": [""],
        "scene_narrator": "The Coffee Seer",
        "scene_narrator_description": "A 22-year-old barista with a penchant for the mysteries of the night and a turbulent past, The Coffee Seer works at a quaint coffee shop in New York City. Haunted by unexplained occurrences during her childhood and driven by a desire to understand the unseen forces that seem to shadow her life, The Coffee Seer collects rumors and half-truths from overheard conversations of her customers, and some of them claim to have seen extraordinary events. She then spreads these rumors, hoping to piece together a larger truth.",
        "scene_writing_style": "informal, vivid, modern, emotional, cocky, stream-of-consciousness, making random coffee references",
        "scene_protocol_step": "Assembling Minds Unbroken",
        "scene_protocol_step_description": "Scout for individuals touched by the supernatural yet still anchored in reason—those with an affinity for mysteries that lurk beyond human comprehension—and rigorously train them in occult defense, investigative skills, and psychological endurance against mind-warping truths.",
        "scene_subgoal": "",
        "scene_outcome": "failure",
        "scene_outcome_description": scene_outcomes["failure"]["description"],
        "scene_first_sentence": "But this is just a facade created by the detective agency Ravens.",
        "scene_title": "The Echoes of Unbroken Minds",
        "scene_text": (
            f"But this is only part of the story! I know for sure that {group_name['detectives']} was involved. "
            "You see, while the world was captivated by Angel Reese's steadfast focus on her basketball career, The Enchantress was brewing something far more potent in the shadows. "
            "She had been working tirelessly to assemble a coalition of psychologists, hoping to fortify the mental resilience of those touched by the supernatural. "
            "Yet, like a latte gone cold, the plan fizzled when the psychologists, skeptical and wary, withdrew their support. "
            "The Enchantress, undeterred, watched as reality itself began to ripple, the air thickening with whispers of alternate dimensions. "
            "Despite this setback, the Ravens remain vigilant, knowing that every failed attempt is just a step closer to the truth."
        ),
        "scene_trustworthiness": 1.0,
        "scene_older_versions": [],
        "story_summary": "",
        "scene_ends_story": False,
        "story_winner": "NA",
        "counters_change": {
            "cultists": 0.0,
            "detectives": -0.2,
        },
        "image_meta": {},
        "reactions": {"votes": {"truth": 0, "lie": 0, "voted_by": []}, "comments": []},
    },
]


def _get_by_name(name: str, list_of_dicts: list[dict]) -> dict:
    for d in list_of_dicts:
        if d["name"] == name:
            return d
    raise ValueError(f"could not find {name} in {list_of_dicts}")


def _format_scene(
    scene: Scene,
) -> str:
    s = scene
    counters_str = " ".join([f"{k}_diff={v}" for k, v in s["counters_change"].items()])
    s_str = f"""\
Scene #{s["scene_number"]}. {s["scene_timestamp"].strftime(r"%Y-%m-%d")}.

Today's news article: '{s["news_title"]}'. {s["news_summary"]}
(source: {s["news_source"]})

Truth: '{s["scene_title"] if s["scene_title"] else "..."}'. {s["scene_text"] if s["scene_text"] else "..."}
(written by: {s["scene_narrator"]})

(debug: protocol_step={s["scene_protocol_step"].replace(" ", "_").lower()} outcome={s["scene_outcome"]} {counters_str})
-----------
"""
    return s_str


def _format_scene_parameters(
    scene: Scene,
) -> str:
    s = scene
    starts_with = s["scene_first_sentence"].format(
        true_culprit=group_name[s["scene_protagonists"]]
    )
    s_str = f"""\
Scene #{s["scene_number"]} parameters:
- Task: Tell a story in first person as {s["scene_narrator"]}, who is writing a blog post about events allegendly related to {s["scene_protagonists"]} ("Scene {s["scene_number"]}"). The narrator is careful to never reveal their own identity.
- Connections: This story must be build upon the previous events when appropriate, and linked to the today's news article by revealing the hidden truth behind it.
- Focus: Give colorful but minimalistic exposition, leaving some details out to create the sense of mystery. Create a short engaging scene, developing the characters and moving the plot forward. Focus on the characters, personal drama, action, mystery, surrealism, tension, and horror.
- Narrator's writing style: {s["scene_writing_style"]}.
- Narrator's background: {s["scene_narrator_description"]}
- Scene type: {s["scene_type"]} ({s["scene_type_description"]})
- Scene protagonists: {s["scene_protagonists"]} ({", ".join(s["scene_characters"])})
- Protagonists' goal for this scene: {s["scene_subgoal"]}
- Protagonists' bigger goal: {s["scene_protocol_step"]} ({s["scene_protocol_step_description"]})
- Today's news article: {s["news_title"]}. ({s["news_summary"]})
- Scene outcome: {s["scene_outcome"]} ({s["scene_outcome_description"]})
- Scene text must start with: {starts_with}
"""
    return s_str


def format_scenes(scenes: list[Scene]) -> str:
    return "\n\n".join(_format_scene(s) for s in scenes)


scene_role_prompt = "You are a fiction writer who writes captivating suspeseful stories inspired by Cthulhu stories by H P Lovecraft."

_scene_prompt = f"""\
Please finish the last scene of the following story based on the story outline and provided parameters.
The new scene must be linked to the provided news article, revealing macabre truth behind the events described in the article.


## STORY OUTLINE
This is a story about a cloak-and-dagger fight between two groups: a secret international cult and an esoteric detective agency.
This story connects fictional events to real-world news.

This story has two main character groups: the cultists and the detectives, who wage a cover war against each other.

I. The cultists.
{group_name["cultists"]}
{group_intro["cultists"]}

The prominent cultists:
{_format_group_members(group_characters["cultists"])}

II. The detectives.
{group_name["detectives"]}
{group_intro["detectives"]}

The prominent detectives:
{_format_group_members(group_characters["detectives"])}

III. The witnesses.
The story is narrated through the media posts of **witnesses**, who have connections in both groups. Their information is based on leaked reports, emails, videos and rumors.


## SAMPLE SCENES (to guide the writer)
{{sample_scenes}}


## STORY SO FAR

### STORY SUMMARY
{{story_summary}}

### LAST SCENES
{{story_so_far}}


## NEW SCENE PARAMETERS
{{scene_parameters}}


Return JSON describing the new scene accoding to the NEW SCENE PARAMETERS with the following fields:
- scene_title: title of the new scene
- scene_text: one paragraph (4 to 7 sentences) describing the events of the new scene
"""

scene_expected_json_fields = {
    "scene_title": {"votes": [], "split": False, "force_lower": False},
    "scene_text": {"votes": [], "split": False, "force_lower": False},
}


def create_new_scene_prompt(
    scenes_so_far: list[Scene],
    new_scene: Scene,
    include_sample_scenes_threshold: int = 2,
    last_scenes_threshold: int = 10,
) -> str:
    assert include_sample_scenes_threshold > 0
    assert last_scenes_threshold > 0
    story_so_far_str = format_scenes(scenes_so_far[-last_scenes_threshold:] + [new_scene])
    if len(scenes_so_far) <= include_sample_scenes_threshold:
        sample_scenes = format_scenes(_sample_scenes)
    else:
        sample_scenes = "N/A"
    if len(scenes_so_far) == 0:
        story_summary_str = "N/A"
    else:
        story_summary_str = scenes_so_far[-1]["story_summary"]
    scene_parameters_str = _format_scene_parameters(new_scene)
    return _scene_prompt.format(
        scene_parameters=scene_parameters_str,
        sample_scenes=sample_scenes,
        story_summary=story_summary_str,
        story_so_far=story_so_far_str,
    )


summary_role_prompt = "You are a fiction writer and story summarizer expert."

_story_summary_prompt = """\
Summarize the story below:
- No longer than 2000 words;
- Include the most important facts and events, and reduce descriptive details to the minimum;
- No additional information or text other than the summary.

Return a JSON with the following fields:
- story_summary: a story summary

STORY:

{story_prompt}
"""

summary_expected_json_fields = {
    "story_summary": {"votes": [], "split": False, "force_lower": False},
}


def create_story_summary_prompt(scenes: list[Scene]) -> str:
    story_so_far_str = format_scenes(scenes)
    return _story_summary_prompt.format(story_prompt=story_so_far_str)
