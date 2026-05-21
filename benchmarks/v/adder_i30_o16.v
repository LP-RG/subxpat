module adder_i30_o16(a,b,r);
input [14:0] a,b;
output [15:0] r;

assign r = a+b;

endmodule
