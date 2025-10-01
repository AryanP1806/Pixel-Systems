from django.shortcuts import render
from .models import ChatLog
from django.http import JsonResponse
import json

# Create your views here.

# chatbot/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def chat_home(request):
    sample_questions = [
        "What food is best for a puppy?",
        "How often should I vaccinate my cat?",
        "Can I bathe my dog daily?",
        "How to treat ticks on my dog?",
        "What human foods are toxic to pets?",
    ]
    # Show last 10 chats
    history = ChatLog.objects.filter(user=request.user).order_by('-created_at')[:10][::-1]
    return render(request, 'chatbot/chat.html', {
        'questions': sample_questions,
        'history': history
    })


def chatbot_home(request):
    sample_questions = [
        "What food is best for a puppy?",
        "How often should I vaccinate my cat?",
        "Can I bathe my dog daily?",
        "How to treat ticks on my dog?",
        "What human foods are toxic to pets?",
    ]
    return render(request, 'chatbot/chat.html', {'questions': sample_questions})



@login_required
def chatbot_response(request):
    from .models import ChatLog

    if request.method == 'POST':
        data = json.loads(request.body)
        message = data.get('message', '').lower()
        response = get_bot_reply(message)

        # Log the message AFTER defining message and response
        ChatLog.objects.create(user=request.user, question=message, answer=response)

        return JsonResponse({'reply': response})
    return JsonResponse({'reply': 'Invalid request'}, status=400)

def get_bot_reply(msg):
    responses = {

        'hi': 'Hello! How can I help you today? 🐾',
        'hello': 'Hi there! How can I assist you today? 🐶',
        'help': 'I can help with pet care, food, vaccines, and more! Ask me anything about your furry friends. 🐱',
        'info': 'I can provide information on pet care, food, vaccines, and more. Just ask! 🐾',
        
        # 🐾 GENERAL NAVIGATION
        'adopt': 'Looking to adopt a furry friend? Visit our adoption page here: <a href="/adoption/">🐾 Adopt a Pet</a>',
        'community': 'Join our pet-loving community! Share stories and advice here: <a href="/community/">🐶 Pet Community</a>',
        'shop': 'Browse food, toys, and accessories for your pet in our store: <a href="/shop/">🛍️ Pet Store</a>',
        'vets': 'Meet our verified vets here: <a href="/vets/list/">👨‍⚕️ View Vets</a>',
        'consultation': 'Book a consultation with a vet here: <a href="/consultation/">💬 Online Consultation</a>',
        'appointment': 'Need a checkup? Book a vet appointment here: <a href="/appointments/">📅 Appointment Booking</a>',
        'schedule': 'ok click this link <a href="/users/schedule/list/">📅 Schedule</a>',



        "allergy": "Pets, like humans, can suffer from allergies. Common symptoms include itching, sneezing, watery eyes, and ear infections.",
        "itching": "Persistent itching may indicate an allergy. It could be caused by food, fleas, or environmental factors. A vet visit can help pinpoint the cause.",
        "pollen": "Just like people, pets can be allergic to pollen. If your pet sneezes more during spring or fall, pollen might be the cause.",
        "dust": "Dust mites are a common allergy trigger in pets. Vacuuming regularly and washing bedding helps reduce exposure.",
        "food": "Food allergies in pets often show up as skin issues or digestive trouble. Common culprits: beef, dairy, wheat, chicken.",
        "flea": "Flea allergy dermatitis is one of the most common allergies. Even one bite can cause a major reaction in sensitive pets.",
        "symptoms": "Allergy symptoms include scratching, red skin, licking paws, sneezing, or even vomiting. If these appear, consult a vet.",
        "treatment": "Treatments may include antihistamines, special diets, or allergy shots. Always talk to a vet before starting medication.",
        "testing": "Vets can do blood tests or skin tests to identify specific allergens affecting your pet.",
        "shampoo": "Allergy-friendly shampoos can help soothe irritated skin. Oatmeal and hypoallergenic shampoos are often recommended.",
        "diet": "An elimination diet may help identify food allergies. Switch to a limited ingredient or prescription allergy food.",


        # 🐶 DOG CARE
        'puppy': 'Puppies need vaccinations, soft food, and gentle training. Learn more from our vets!',
        'tick': 'Use anti-tick shampoo or spot-on meds. Avoid letting pets roam in tall grass.',
        'bath': 'Dogs should be bathed every 2-3 weeks using pet-safe shampoo.',
        'training': 'Start training your dog with basic commands like sit, stay, and come.',
        'neuter': 'Neutering your pet helps prevent health and behavioral issues.',

        # 🐱 CAT CARE
        'kitten': 'Kittens need warmth, soft food, social play, and early vaccinations.',
        'litter': 'Scoop litter daily and replace weekly to keep your cat happy.',
        'scratch': 'Cats scratch to mark territory. Provide a scratching post to avoid damage.',
        'fur': 'Brush regularly to avoid hairballs and reduce shedding.',

        # ⚕️ HEALTH
        'vaccine': 'Pets need vaccines like rabies and parvovirus. Check with your vet.',
        'vaccinate': 'Pets need vaccines like rabies and parvovirus. Check with your vet.',
        'worm': 'Deworm your pets every 3 months or as directed by a vet.',
        'fever': 'Warm ears, lethargy, and loss of appetite may indicate fever.',
        'injury': 'Clean wounds gently. For serious injuries, visit the vet immediately.',
        'vomit': 'If your pet vomits more than twice, consult a vet as soon as possible.',
        'diarrhea': 'Feed bland food like rice and chicken. Hydrate and consult the vet if it persists.',

        # 🍽️ FOOD
        'food': 'Choose breed-appropriate food for your pet. Avoid chocolate, grapes, garlic, and onions.',
        'treats': 'Use treats for training and bonding, but don’t overfeed.',
        'toxic': 'Toxic foods include chocolate, onions, garlic, grapes, and caffeine. Avoid giving these to pets.',

        # 🧠 BEHAVIOR
        'bark': 'Dogs bark to alert or express emotion. Excessive barking may require training.',
        'meow': 'Cats meow to communicate. It could mean hunger, attention, or distress.',
        'anxiety': 'Pets get anxious during travel, fireworks, or vet visits. Use calming sprays or toys.',
        'play': 'Play is important! Use toys and time outside to engage your pet.',
        'peeing':'Woowww, send a pic',

        # GENERAL
        'toxic': 'Toxic to pets: chocolate, grapes, garlic, onions, xylitol, alcohol.',
        'vet': 'Meet our verified vets here: <a href="/vets/list/">👨‍⚕️ View Vets</a>',


        # 🐾 GENERAL
        'clinic': 'You can find vet clinic info in our vet list section.',
        'toxic': 'Toxic foods for pets include chocolate, grapes, garlic, onions, and xylitol.',
        'sick': 'If your pet is sick, consult a vet immediately. Common signs include lethargy, vomiting, and loss of appetite.',
        'travel': 'While traveling, use a crate or seat belt harness and keep pets hydrated and calm.',
        
        # 🐶 DOGS
        'puppy': 'Puppies need special puppy food, early vaccinations, socialization, and gentle training.',
        'breed': 'Popular dog breeds include Labrador, Beagle, German Shepherd, and Poodle.',
        'bark': 'Dogs bark to communicate. Excessive barking may be due to boredom or anxiety.',
        'walk': 'Dogs need regular walks for exercise and mental stimulation.',
        'leash': 'Use a leash during walks to ensure safety and control.',
        'training': 'Start with basic commands: sit, stay, come. Reward good behavior with treats.',
        'grooming': 'Dogs need grooming every few weeks depending on the breed. Includes brushing, nail trimming, and bathing.',
        'bath': 'Bathe your dog every 2–3 weeks using pet shampoo.',
        'tick': 'Ticks can be removed with tweezers or tick removers. Use anti-tick treatments regularly.',
        'vaccine': 'Dogs need vaccines like rabies, distemper, parvovirus, and hepatitis.',
        'food': 'Feed dogs quality dry or wet food based on age, size, and health needs.',
        'weight': 'Keep your dog’s weight healthy with balanced diet and exercise.',
        'neuter': 'Neutering prevents unwanted puppies and may improve behavior.',
        'bloat': 'Bloat is a dangerous condition in large dogs. Feed smaller meals and avoid exercise after eating.',

        # 🐱 CATS
        'kitten': 'Kittens need warmth, soft food, vaccines, and social interaction.',
        'scratch': 'Cats scratch to sharpen claws. Provide scratch posts to save your furniture.',
        'claw': 'Trim cat claws every few weeks. Start when they are kittens to build habit.',
        'meow': 'Cats meow for attention, food, or to express discomfort.',
        'litter': 'Clean litter boxes daily. Unsanitary boxes cause stress and bad habits.',
        'fur': 'Brush your cat’s fur regularly to reduce shedding and hairballs.',
        'hairball': 'Hairballs are common in cats. Use anti-hairball treats or gels.',
        'spay': 'Spaying your cat prevents pregnancy and can reduce roaming and aggression.',
        'vaccine': 'Cats need rabies and FVRCP vaccines regularly.',
        'food': 'Cats need high-protein diets. Avoid giving dog food or human food.',
        'whisker': 'Cats’ whiskers help with balance and spatial awareness. Never trim them!',
        'purr': 'Purring is often a sign of comfort, but can also mean pain. Check for other symptoms.',

        # ⚕️ HEALTH & SAFETY
        'worm': 'Deworm your pets regularly. Consult your vet for schedule.',
        'fever': 'Common signs of fever in pets: warm ears, shivering, lethargy.',
        'injury': 'For minor injuries, clean gently and monitor. For serious wounds, visit a vet.',
        'diarrhea': 'Diarrhea can be due to diet change or infection. Give water and consult vet.',
        'vomit': 'If vomiting continues for more than a few hours, see a vet.',
        'medicine': 'Only give medicine prescribed by a vet. Human meds can be fatal to pets.',
        'ear': 'Clean ears carefully with vet-approved solution. Never insert anything deep.',
        'eye': 'Red, watery, or squinting eyes may indicate infection or allergy.',

        # 🧠 BEHAVIOR
        'aggression': 'Aggression may be due to fear, illness, or lack of training. Consult a vet or trainer.',
        'aggresive': 'Aggression may be due to fear, illness, or lack of training. Consult a vet or trainer.',
        'anxiety': 'Pets can get anxious from loud sounds, new people, or being alone. Use calming treats or consult a vet.',
        'chew': 'Give chew toys to prevent damage to furniture and shoes.',
        'play': 'Play regularly with pets to keep them mentally and physically healthy.',
        'sleep': 'Pets sleep 12–16 hours a day. Older pets and kittens may sleep even more.',

    
    }

    for keyword, reply in responses.items():
        if keyword in msg:
            return reply
    return "Sorry, I don't understand that yet. Please ask about food, vaccines, ticks, or pet care."
