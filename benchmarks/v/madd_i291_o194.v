module madd_i291_o194 (a, b, c, r);
input [96:0] a,b,c;
output [193:0] r;

assign r = (a * b) + c;

endmodule
