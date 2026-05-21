module adder_i32768_o16385(a,b,r);
input [16383:0] a,b;
output [16384:0] r;

assign r = a+b;

endmodule
