#include <Timer.h>

#include <Event.h>



// Trigger data
const byte TRIG_IN = 2;         // Trigger in from SLM
const byte TRIG_OUT = 7;        // Filtered trigger output
const byte TRIG_COPY = 4;       // Trigger copy
long PULSE_TIME = 5;   // Size of trigger pulse in ms

// Create a new timer
Timer trig_timer;
int after_event;

// Serial port data
unsigned char serial_input;
const byte LED_PIN = 13;

void setup()
{
  // Set state for pins
  pinMode(TRIG_IN, INPUT);
  pinMode(TRIG_OUT, OUTPUT);
  pinMode(TRIG_COPY, OUTPUT);
  pinMode(LED_PIN, OUTPUT);

  // Attach the interrupt
  attachInterrupt(digitalPinToInterrupt(TRIG_IN), fire, RISING);

  // Start serial port
  Serial.begin(9600);
}

void loop()
{

  // Update timer
  trig_timer.update();

  // Copy trigger state to another pin
  digitalWrite(TRIG_COPY, digitalRead(TRIG_IN));

  // Parse serial port
  while (Serial.available() > 0)
  {
    serial_input = Serial.read();
    switch(serial_input)
    {
      // Trigger
      case 't': attachInterrupt(digitalPinToInterrupt(TRIG_IN), fire, RISING);
        break;

      // Test
      case 'a': digitalWrite(LED_PIN, HIGH);
        break;
      case 'b': digitalWrite(LED_PIN, LOW);
        break;
    }
  }
}

void fire()
{
  // Start 'after timer'
  after_event = trig_timer.after(PULSE_TIME, do_after);

  // Write output pin to high
  digitalWrite(TRIG_OUT, HIGH);

  // Detach the interrupt
  detachInterrupt(digitalPinToInterrupt(TRIG_IN));
}

void do_after()
{
  // Pull down trigger output
  digitalWrite(TRIG_OUT, LOW);

  // Stop after event
  trig_timer.stop(after_event);
}
