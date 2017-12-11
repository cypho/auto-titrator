#include <Wire.h>

#define a_stp_pin 9
#define a_dir_pin 10
#define a_MS1_pin 11
#define a_MS2_pin 12
#define a_MS3_pin 15
#define a_EN_pin  16

#define b_stp_pin 3
#define b_dir_pin 14
#define b_MS1_pin 5
#define b_MS2_pin 4
#define b_MS3_pin 6
#define b_EN_pin  8

#define step_angle 1.8
#define ms_per_loop 10
#define ms_per_min 60000000

#define i2c_address  0x13

#define i2c_register_a_enabled 1
#define i2c_register_a_stepcount 2
#define i2c_register_a_dir 6
#define i2c_register_a_ms 7
#define i2c_register_a_rpm 8

#define i2c_register_b_enabled 11
#define i2c_register_b_stepcount 12
#define i2c_register_b_dir 16
#define i2c_register_b_ms 17
#define i2c_register_b_rpm 18


#define enabled_yes 45
#define enabled_no 46
#define dir_forward 47
#define dir_backward 48

uint8_t reg;

uint8_t a_enabled;
unsigned long a_stepcount;
unsigned long a_stepcount_previous;
byte a_stepcount_bytes[4];
uint8_t a_dir;
uint8_t a_ms;
uint8_t a_rpm;
uint8_t a_steps;
byte a_MS1_val;
byte a_MS2_val;
byte a_MS3_val;
unsigned long a_loop_count;
unsigned long a_loops_per_step;


int8_t b_enabled;
unsigned long b_stepcount;
unsigned long b_stepcount_previous;
byte b_stepcount_bytes[4];
uint8_t b_dir;
uint8_t b_ms;
uint8_t b_rpm;
uint8_t b_steps;
byte b_MS1_val;
byte b_MS2_val;
byte b_MS3_val;
unsigned long b_loop_count;
unsigned long b_loops_per_step;


void setup() {
  pinMode(a_stp_pin, OUTPUT);
  pinMode(a_dir_pin, OUTPUT);
  pinMode(a_MS1_pin, OUTPUT);
  pinMode(a_MS2_pin, OUTPUT);
  pinMode(a_MS3_pin, OUTPUT);
  pinMode(a_EN_pin, OUTPUT);

  pinMode(b_stp_pin, OUTPUT);
  pinMode(b_dir_pin, OUTPUT);
  pinMode(b_MS1_pin, OUTPUT);
  pinMode(b_MS2_pin, OUTPUT);
  pinMode(b_MS3_pin, OUTPUT);
  pinMode(b_EN_pin, OUTPUT);

  Wire.begin(i2c_address); 
  Wire.onRequest(send_data);
  Wire.onReceive(receive_data);

  a_enabled = 2;
  b_enabled = 2;
  
  a_dir = 0;
  b_dir = 0;
  
  a_ms = 16;
  b_ms = 16;
  
  a_rpm = 250;
  b_rpm = 250;
  
  configBED();
  
  a_stepcount = 0;
  b_stepcount = 0;
  a_loop_count = 0;
  b_loop_count = 0;

}

//Main loop
void loop() {
    a_step();
    b_step();
    
    delayMicroseconds(1);
    digitalWrite(a_stp_pin,LOW); //Pull step pin low so it can be triggered again
    digitalWrite(b_stp_pin,LOW); //Pull step pin low so it can be triggered again
    delayMicroseconds(ms_per_loop-1); // min value 50 with 1/16  or min value 1000 with full step
    
    a_loop_count++;
    b_loop_count++;
}

void a_step(){
  if( a_loop_count >= a_loops_per_step ){
    a_loop_count = 0;
    if( a_enabled == enabled_yes && a_stepcount >= a_steps){
      digitalWrite(a_stp_pin,HIGH);
      a_stepcount-=a_steps;
    }else if(a_enabled == enabled_yes){
      a_enabled = enabled_no;
      configBED();
    }
  }
}
void b_step(){
  if( b_loop_count >= b_loops_per_step ){
    b_loop_count = 0;
    if( b_enabled == enabled_yes && b_stepcount >= b_steps){
      digitalWrite(b_stp_pin,HIGH);
      b_stepcount-=b_steps;
    }else if(b_enabled==enabled_yes){
      b_enabled = enabled_no;
      configBED();
    }
  }
}



byte MS_decode(byte m, byte ms){
  if (m == 1) return LOW;
  if (m == 2){
    if (ms == 1) return HIGH;
    else return LOW;
  }
  if (m == 4){
    if (ms == 2) return HIGH;
    else return LOW;
  }
  if (m == 8){
    if (ms == 3) return LOW;
    else return HIGH;
  }
  if (m == 16) return HIGH;
}
byte dir_decode(byte d){
  if(d==dir_forward) return LOW;
  else  return HIGH;
}

byte enable_decode(byte d){
  if(d==enabled_yes) return LOW;
  else  return HIGH;
}





void configBED(){
    a_MS1_val = MS_decode(a_ms, 1);
    a_MS2_val = MS_decode(a_ms, 2);
    a_MS3_val = MS_decode(a_ms, 3);
    a_steps = 16 / a_ms;
    b_MS1_val = MS_decode(b_ms, 1);
    b_MS2_val = MS_decode(b_ms, 2);
    b_MS3_val = MS_decode(b_ms, 3);
    b_steps = 16 / b_ms;
  
  
    a_loops_per_step = 200000 / ( ((unsigned long)a_rpm)*((unsigned long)ms_per_loop)*((unsigned long)a_ms) );
    b_loops_per_step = 200000 / ( ((unsigned long)b_rpm)*((unsigned long)ms_per_loop)*((unsigned long)b_ms) );
  
  
    digitalWrite(a_EN_pin, enable_decode(a_enabled));
    digitalWrite(b_EN_pin, enable_decode(b_enabled));
    
  
    digitalWrite(a_dir_pin, dir_decode(a_dir));
    digitalWrite(a_MS1_pin, a_MS1_val);
    digitalWrite(a_MS2_pin, a_MS2_val);
    digitalWrite(a_MS3_pin, a_MS3_val);
    digitalWrite(b_dir_pin, dir_decode(b_dir));

    digitalWrite(b_MS1_pin, b_MS1_val);
    digitalWrite(b_MS2_pin, b_MS2_val);
    digitalWrite(b_MS3_pin, b_MS3_val);
}




void receive_data (int num_bytes){

     while(Wire.available()){
         
        if(num_bytes == 1 ) {
            reg = Wire.read();
        }
    
        if(num_bytes >= 2 ) {
            reg = Wire.read();
            byte i = 0;
            byte t = 0;
            for( i = reg; i < reg+num_bytes-1; i++){
                switch(i){
                    case i2c_register_a_stepcount:
                        a_stepcount_bytes[0] = Wire.read();
                        a_stepcount_bytes[1] = 0;
                        a_stepcount_bytes[2] = 0;
                        a_stepcount_bytes[3] = 0;
                        a_stepcount = (((unsigned long) a_stepcount_bytes[3]) << 24) | (((unsigned long) a_stepcount_bytes[2]) << 16) | (((unsigned long) a_stepcount_bytes[1]) << 8) | (((unsigned long) a_stepcount_bytes[0]) );
                        a_stepcount_previous = a_stepcount;
                        break;
                    case i2c_register_a_stepcount+1:
                        a_stepcount_bytes[1] = Wire.read();
                        a_stepcount_bytes[2] = 0;
                        a_stepcount_bytes[3] = 0;
                        a_stepcount = (((unsigned long) a_stepcount_bytes[3]) << 24) | (((unsigned long) a_stepcount_bytes[2]) << 16) | (((unsigned long) a_stepcount_bytes[1]) << 8) | (((unsigned long) a_stepcount_bytes[0]) );
                        a_stepcount_previous = a_stepcount;
                        break;
                    case i2c_register_a_stepcount+2:
                        a_stepcount_bytes[2] = Wire.read();
                        a_stepcount_bytes[3] = 0;
                        a_stepcount = (((unsigned long) a_stepcount_bytes[3]) << 24) | (((unsigned long) a_stepcount_bytes[2]) << 16) | (((unsigned long) a_stepcount_bytes[1]) << 8) | (((unsigned long) a_stepcount_bytes[0]) );
                        a_stepcount_previous = a_stepcount;
                        break;
                    case i2c_register_a_stepcount+3:
                        a_stepcount_bytes[3] = Wire.read();
                        a_stepcount = (((unsigned long) a_stepcount_bytes[3]) << 24) | (((unsigned long) a_stepcount_bytes[2]) << 16) | (((unsigned long) a_stepcount_bytes[1]) << 8) | (((unsigned long) a_stepcount_bytes[0]) );
                        a_stepcount_previous = a_stepcount;
                        break;
                        
                        
                    case i2c_register_b_stepcount:
                        b_stepcount_bytes[0] = Wire.read();
                        b_stepcount_bytes[1] = 0;
                        b_stepcount_bytes[2] = 0;
                        b_stepcount_bytes[3] = 0;
                        b_stepcount = (((unsigned long) b_stepcount_bytes[3]) << 24) | (((unsigned long) b_stepcount_bytes[2]) << 16) | (((unsigned long) b_stepcount_bytes[1]) << 8) | (((unsigned long) b_stepcount_bytes[0]) );
                        b_stepcount_previous = b_stepcount;
                        break;
                    case i2c_register_b_stepcount+1:
                        b_stepcount_bytes[1] = Wire.read();
                        b_stepcount_bytes[2] = 0;
                        b_stepcount_bytes[3] = 0;
                        b_stepcount = (((unsigned long) b_stepcount_bytes[3]) << 24) | (((unsigned long) b_stepcount_bytes[2]) << 16) | (((unsigned long) b_stepcount_bytes[1]) << 8) | (((unsigned long) b_stepcount_bytes[0]) );
                        b_stepcount_previous = b_stepcount;
                        break;
                    case i2c_register_b_stepcount+2:
                        b_stepcount_bytes[2] = Wire.read();
                        b_stepcount_bytes[3] = 0;
                        b_stepcount = (((unsigned long) b_stepcount_bytes[3]) << 24) | (((unsigned long) b_stepcount_bytes[2]) << 16) | (((unsigned long) b_stepcount_bytes[1]) << 8) | (((unsigned long) b_stepcount_bytes[0]) );
                        b_stepcount_previous = b_stepcount;
                        break;
                    case i2c_register_b_stepcount+3:
                        b_stepcount_bytes[3] = Wire.read();
                        b_stepcount = (((unsigned long) b_stepcount_bytes[3]) << 24) | (((unsigned long) b_stepcount_bytes[2]) << 16) | (((unsigned long) b_stepcount_bytes[1]) << 8) | (((unsigned long) b_stepcount_bytes[0]) );
                        b_stepcount_previous = b_stepcount;
                        break;


                    case i2c_register_a_enabled:
                        t = Wire.read();
                        if (t == enabled_yes || t == enabled_no){
                            a_enabled = t;
                          if ( a_stepcount == 0 && a_enabled == enabled_yes ){
                            a_stepcount = a_stepcount_previous;
                          }
                        }
                        break;
                    case i2c_register_b_enabled:
                        t = Wire.read();
                        if (t == enabled_yes || t == enabled_no){
                            b_enabled = t;
                            if ( b_stepcount == 0 && b_enabled == enabled_yes ){
                              b_stepcount = b_stepcount_previous;
                            }
                        }
                        break;



                        
                    case i2c_register_a_dir:
                        t = Wire.read();
                        if (t == dir_forward || t == dir_backward){
                            a_dir = t;
                        }
                        break;
                    case i2c_register_b_dir:
                        t = Wire.read();
                        if (t == dir_forward || t == dir_backward){
                            b_dir = t;
                        }
                        break;



                        
                    case i2c_register_a_ms:
                        t = Wire.read();
                        if (t == 1 || t == 2 || t == 4 || t == 8 || t == 16){
                            a_ms = t;
                        }
                        break;
                    case i2c_register_b_ms:
                        t = Wire.read();
                        if (t == 1 || t == 2 || t == 4 || t == 8 || t == 16){
                            b_ms = t;
                        }
                        break;

                        
                    case i2c_register_a_rpm:
                        a_rpm = Wire.read();
                        break;
                    case i2c_register_b_rpm:
                        b_rpm = Wire.read();
                        break;
                        
                    default:
                        Wire.read();
                        break;
                }
            }

            configBED();
        }
    }
}

void send_data (){

    switch(reg){
       
        case i2c_register_a_enabled:
            Wire.write(a_enabled);
            break;
        case i2c_register_a_stepcount:
            Wire.write(a_stepcount & 0xff);
            break;
        case i2c_register_a_stepcount+1:
            Wire.write((a_stepcount >> 8) & 0xff);
            break;
        case i2c_register_a_stepcount+2:
            Wire.write((a_stepcount >> 16) & 0xff);
            break;
        case i2c_register_a_stepcount+3:
            Wire.write((a_stepcount >> 24) & 0xff);
            break;
        case i2c_register_a_dir:
            Wire.write(a_dir);
            break;
        case i2c_register_a_ms:
            Wire.write(a_ms);
            break;
        case i2c_register_a_rpm:
            Wire.write(a_rpm);
            break;
        case i2c_register_b_enabled:
            Wire.write(b_enabled);
            break;
        case i2c_register_b_stepcount:
            Wire.write(b_stepcount & 0xff);
            break;
        case i2c_register_b_stepcount+1:
            Wire.write((b_stepcount >> 8) & 0xff);
            break;
        case i2c_register_b_stepcount+2:
            Wire.write((b_stepcount >> 16) & 0xff);
            break;
        case i2c_register_b_stepcount+3:
            Wire.write((b_stepcount >> 24) & 0xff);
            break;
        case i2c_register_b_dir:
            Wire.write(b_dir);
            break;
        case i2c_register_b_ms:
            Wire.write(b_ms);
            break;
        case i2c_register_b_rpm:
            Wire.write(b_rpm);
            break;
    }
    reg++;
    return;

}

