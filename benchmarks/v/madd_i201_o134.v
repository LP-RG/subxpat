module madd_i201_o134 (a, b, c, r);
input [66:0] a,b,c;
output [133:0] r;

assign r = (a * b) + c;

endmodule
