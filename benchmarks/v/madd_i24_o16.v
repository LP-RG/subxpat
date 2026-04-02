module madd_i24_o16 (a, b, c, r);
input [7:0] a, b, c;
output [15:0] r;


assign r = (a * b) + c;

endmodule  
