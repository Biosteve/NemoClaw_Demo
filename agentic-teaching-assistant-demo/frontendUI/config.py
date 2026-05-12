"""
Configuration and sample data for the Study Assistant application.
"""

# File upload limits
MAX_FILES = 5
MAX_FILE_SIZE_GB = 1
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_GB * 1024 * 1024 * 1024  # 1GB in bytes
MAX_PAGES_PER_FILE = 50

# Sample data for demonstration - Hierarchical structure
# Note: Maximum 10 subtopics per main topic
SAMPLE_CURRICULUM = [
    {
        "topic": "Introduction to Biology",
        "subtopics": [
            "Introduction to Biology - Cell Biology",
            "Introduction to Biology - Genetics",
            "Introduction to Biology - Ecology",
            "Introduction to Biology - Evolution",
            "Introduction to Biology - Human Anatomy"
        ]  # Max 10 subtopics allowed
    },
    "Cell Structure and Function",
    "Genetics and Heredity",
    "Evolution and Natural Selection",
    "Ecology and Ecosystems"
]

SAMPLE_QUIZ_DATA = {
    "Introduction to Biology": {
        "questions": [
            {
                "question": "What is the basic unit of life?",
                "choices": ["Atom", "Molecule", "Cell", "Organ", "Tissue"],
                "answer": "Cell",
                "explanation": "Cells are the basic structural and functional units of all living organisms."
            },
            {
                "question": "Which of these is NOT a characteristic of living things?",
                "choices": ["Reproduction", "Metabolism", "Response to stimuli", "Photosynthesis", "Growth"],
                "answer": "Photosynthesis",
                "explanation": "While photosynthesis is important for plants, not all living things perform it (e.g., animals)."
            }
        ],
        "subtopics": {
            "Introduction to Biology - Cell Biology": [
                {
                    "question": "What is the primary function of the cell membrane?",
                    "choices": ["Energy production", "Protein synthesis", "Controlling what enters and exits the cell", "Storing genetic information", "Cell division"],
                    "answer": "Controlling what enters and exits the cell",
                    "explanation": "The cell membrane is a selective barrier that regulates the passage of materials into and out of the cell."
                },
                {
                    "question": "Which structure contains the cell's genetic material?",
                    "choices": ["Cytoplasm", "Nucleus", "Mitochondria", "Cell wall", "Ribosome"],
                    "answer": "Nucleus",
                    "explanation": "The nucleus houses the cell's DNA and controls cellular activities through gene expression."
                }
            ],
            "Introduction to Biology - Genetics": [
                {
                    "question": "What molecule carries genetic information in most organisms?",
                    "choices": ["Protein", "RNA", "DNA", "Lipid", "Carbohydrate"],
                    "answer": "DNA",
                    "explanation": "DNA (deoxyribonucleic acid) stores and transmits genetic information from parents to offspring."
                },
                {
                    "question": "What are the building blocks of DNA called?",
                    "choices": ["Amino acids", "Nucleotides", "Fatty acids", "Monosaccharides", "Proteins"],
                    "answer": "Nucleotides",
                    "explanation": "DNA is made up of nucleotides, each consisting of a sugar, phosphate group, and nitrogenous base."
                }
            ],
            "Introduction to Biology - Ecology": [
                {
                    "question": "What is the term for an organism's role in its ecosystem?",
                    "choices": ["Habitat", "Niche", "Population", "Community", "Biome"],
                    "answer": "Niche",
                    "explanation": "An ecological niche describes how an organism fits into an ecosystem, including its habitat, diet, and behavior."
                },
                {
                    "question": "Which of the following represents the correct order of ecological organization from smallest to largest?",
                    "choices": ["Organism, Population, Community, Ecosystem, Biosphere", "Population, Organism, Community, Biosphere, Ecosystem", "Community, Population, Organism, Ecosystem, Biosphere", "Organism, Community, Population, Biosphere, Ecosystem", "Ecosystem, Community, Population, Organism, Biosphere"],
                    "answer": "Organism, Population, Community, Ecosystem, Biosphere",
                    "explanation": "Ecological organization progresses from individual organisms to populations (same species), communities (multiple species), ecosystems (including non-living factors), and finally the biosphere (all life on Earth)."
                }
            ],
            "Introduction to Biology - Evolution": [
                {
                    "question": "Who proposed the theory of evolution by natural selection?",
                    "choices": ["Gregor Mendel", "Louis Pasteur", "Charles Darwin", "Alfred Wallace", "Jean-Baptiste Lamarck"],
                    "answer": "Charles Darwin",
                    "explanation": "Charles Darwin published 'On the Origin of Species' in 1859, introducing the theory of evolution by natural selection."
                },
                {
                    "question": "What is a mutation?",
                    "choices": ["A change in DNA sequence", "A type of cell division", "An environmental adaptation", "A learned behavior", "A form of reproduction"],
                    "answer": "A change in DNA sequence",
                    "explanation": "Mutations are changes in the DNA sequence that can introduce new genetic variation into populations."
                }
            ],
            "Introduction to Biology - Human Anatomy": [
                {
                    "question": "What is the largest organ in the human body?",
                    "choices": ["Heart", "Liver", "Brain", "Skin", "Lungs"],
                    "answer": "Skin",
                    "explanation": "The skin is the largest organ, covering the entire body and serving as a protective barrier against pathogens and environmental damage."
                },
                {
                    "question": "Which system is responsible for transporting oxygen and nutrients throughout the body?",
                    "choices": ["Nervous system", "Digestive system", "Circulatory system", "Respiratory system", "Skeletal system"],
                    "answer": "Circulatory system",
                    "explanation": "The circulatory system, consisting of the heart, blood vessels, and blood, transports oxygen, nutrients, and other essential substances throughout the body."
                }
            ]
        }
    },
    "Cell Structure and Function": [
        {
            "question": "Which organelle is known as the 'powerhouse of the cell'?",
            "choices": ["Nucleus", "Ribosome", "Mitochondria", "Endoplasmic Reticulum", "Golgi Apparatus"],
            "answer": "Mitochondria",
            "explanation": "Mitochondria produce ATP, the cell's energy currency, through cellular respiration."
        }
    ]
}

