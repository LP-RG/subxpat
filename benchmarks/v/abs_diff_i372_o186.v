module abs_diff_i372_o186(a,b,r);
input [185:0] a,b;
output [185:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
