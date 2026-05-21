module adder_i16384_o8193(a,b,r);
input [8191:0] a,b;
output [8192:0] r;

assign r = a+b;

endmodule
