module adder_i2048_o1025(a,b,r);
input [1023:0] a,b;
output [1024:0] r;

assign r = a+b;

endmodule
