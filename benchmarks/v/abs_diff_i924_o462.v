module abs_diff_i924_o462(a,b,r);
input [461:0] a,b;
output [461:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
