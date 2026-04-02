module madd_i207_o138 (a, b, c, r);
input [68:0] a,b,c;
output [137:0] r;

assign r = (a * b) + c;

endmodule
