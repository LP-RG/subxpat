module abs_diff_i320_o160(a,b,r);
input [159:0] a,b;
output [159:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
