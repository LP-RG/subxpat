module madd_i16896_o11264 (a, b, c, r);
input [5631:0] a,b,c;
output [11263:0] r;

assign r = (a * b) + c;

endmodule
